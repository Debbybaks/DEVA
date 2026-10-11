import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import numpy as np
from deva.schema import Problem
from deva.model import Scenario, simulate, synthesise, incidence
from deva.scenarios import declared, sampled
from deva.verification import verify, wilson
from deva.experiment import run, canonical

ROOT = Path(__file__).resolve().parents[1]


def chain():
    return dict(id='chain', objective='Known analytical flow', nodes=['s', 'j', 'd'],
                supply={'s': 20}, demand={'d': 10}, budget=100, target=.95,
                edges=[dict(id='a', tail='s', head='j', unit_cost=1, max_capacity=20, corridor='one'),
                       dict(id='b', tail='j', head='d', unit_cost=1, max_capacity=20, corridor='two')])


class AnalyticalTests(unittest.TestCase):
    def setUp(self):
        self.p = Problem.parse(chain())
        self.nominal = Scenario('nominal', (1., 1.))

    def test_chain_bottleneck(self):
        result = simulate(self.p, [7, 4], self.nominal)
        self.assertAlmostEqual(result['service_fraction'], .4, places=7)
        np.testing.assert_allclose(result['flow'], [4, 4], atol=1e-7)

    def test_disconnected(self):
        self.assertEqual(simulate(self.p, [0, 20], self.nominal)['service_fraction'], 0)

    def test_supply_bound(self):
        result = simulate(self.p, [20, 20], Scenario('shortage', (1., 1.), supply_factor=.2))
        self.assertAlmostEqual(result['service_fraction'], .4)

    def test_parallel_known_sum(self):
        raw = chain(); raw['edges'][1].update(tail='s', head='j'); raw['demand']={'j':10}
        p = Problem.parse(raw)
        self.assertAlmostEqual(simulate(p, [3, 4], self.nominal)['service_fraction'], .7)

    def test_design_known_cost(self):
        result = synthesise(self.p, [self.nominal])
        np.testing.assert_allclose(result['capacities'], [9.5, 9.5], atol=1e-7)
        self.assertAlmostEqual(result['cost'], 19)

    def test_budget_and_outage_infeasible(self):
        self.assertEqual(synthesise(self.p, [Scenario('loss', (0., 1.))])['status'], 'infeasible')
        raw=chain(); raw['budget']=18
        self.assertEqual(synthesise(Problem.parse(raw), [self.nominal])['status'], 'infeasible')

    def test_seeded_invariants_and_monotonicity(self):
        rng=np.random.default_rng(7)
        for _ in range(30):
            capacities=rng.uniform(0, 15, 2)
            result=simulate(self.p, capacities, self.nominal)
            expected=min(1, min(capacities)/10)
            self.assertAlmostEqual(result['service_fraction'], expected, places=7)
            residual=incidence(self.p) @ result['flow'] + result['injection'] - np.array(result['delivered'])
            np.testing.assert_allclose(residual, 0, atol=1e-7)
            better=simulate(self.p, capacities+1, self.nominal)
            self.assertGreaterEqual(better['service_fraction']+1e-7, result['service_fraction'])

    def test_no_false_verification(self):
        results=[simulate(self.p, [10,10], self.nominal), simulate(self.p, [10,10], Scenario('loss', (0.,1.)))]
        v=verify(self.p, [10,10], results)
        self.assertEqual(v['level'], 'STRESS TESTED')
        self.assertFalse(v['requirements_pass'])
        self.assertFalse(v['formal_verification'])

    def test_invalid_capacity_and_scenario(self):
        for c in ([float('nan'),1], [-1,1], [21,1], [1]):
            with self.assertRaises(ValueError): simulate(self.p,c,self.nominal)
        with self.assertRaises(ValueError): simulate(self.p,[1,1],Scenario('bad',(2.,1.)))


class InputAndStatisticsTests(unittest.TestCase):
    def test_strict_input(self):
        for mutate in (lambda r:r.update(extra=1),lambda r:r.update(budget=float('nan')),
                       lambda r:r.update(target=True),lambda r:r.update(nodes=['s','s']),
                       lambda r:r['edges'][0].update(tail='absent')):
            raw=chain(); mutate(raw)
            with self.assertRaises(ValueError): Problem.parse(raw)

    def test_wilson_edges(self):
        low, high=wilson(0,100)
        self.assertAlmostEqual(low,0)
        self.assertAlmostEqual(high,.03699349820698568)
        a,b=wilson(100,100)
        self.assertAlmostEqual(a,1-high); self.assertAlmostEqual(b,1)
        with self.assertRaises(ValueError): wilson(0,0)

    def test_sampling_replay_and_caps(self):
        p=Problem.parse(chain())
        self.assertEqual(sampled(p,4,10),sampled(p,4,10))
        self.assertNotEqual(sampled(p,4,10),sampled(p,5,10))
        for count in (0,10001,True):
            with self.assertRaises(ValueError): sampled(p,4,count)


class IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=json.loads((ROOT/'examples/emergency_water.json').read_text())
        cls.evidence=run(cls.raw,42,40)

    def test_robust_synthesis_and_negative_evidence(self):
        s=self.evidence['science']; candidates={c['id']:c for c in s['candidates']}
        self.assertEqual(s['winner'],'robust-lp')
        robust=candidates['robust-lp']
        self.assertAlmostEqual(robust['verification']['cost'],399,places=5)
        self.assertEqual(robust['verification']['level'],'ROBUST UNDER TESTED CONDITIONS')
        self.assertTrue(all(r['passes'] for r in robust['declared_results']))
        self.assertEqual(candidates['nominal-lp']['disposition'],'rejected')
        self.assertTrue(candidates['nominal-lp']['counterexamples'])
        self.assertEqual(len(robust['heldout_results']),40)
        self.assertGreater(robust['uncertainty']['failures'],0)

    def test_reproducibility_and_hash(self):
        second=run(self.raw,42,40)
        self.assertEqual(self.evidence['science'],second['science'])
        self.assertEqual(self.evidence['experiment_id'],second['experiment_id'])
        self.assertNotEqual(self.evidence['timestamp'],second['timestamp'])
        expected=hashlib.sha256(canonical(second['science']).encode()).hexdigest()
        self.assertEqual(expected,second['scientific_sha256'])

    def test_no_survivor_is_valid_outcome(self):
        raw=chain(); result=run(raw,3,5)
        self.assertIsNone(result['science']['winner'])
        robust=result['science']['candidates'][-1]
        self.assertEqual(robust['synthesis']['status'],'infeasible')
        self.assertEqual(robust['verification']['level'],'UNTESTED')

    def test_cli_export_and_invalid_input(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'evidence.json'
            cmd=[sys.executable,'-m','deva.cli',str(ROOT/'examples/emergency_water.json'),'--samples','5','--output',str(output)]
            process=subprocess.run(cmd,capture_output=True,text=True)
            self.assertEqual(process.returncode,0,process.stderr)
            data=json.loads(output.read_text())
            self.assertEqual(data['science']['sample_count'],5)
            bad=Path(directory)/'bad.json'; bad.write_text('{"id": "a", "id": "b"}')
            cmd[3]=str(bad)
            process=subprocess.run(cmd,capture_output=True,text=True)
            self.assertNotEqual(process.returncode,0)
            self.assertIn('Duplicate JSON key',process.stderr)


if __name__=='__main__': unittest.main()
