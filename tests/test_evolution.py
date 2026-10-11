import copy
import json
from pathlib import Path
import unittest
from deva.adversary import topology_cuts,critical_demand,discover
from deva.audit import audit_result,verify_hash,ancestors
from deva.evolution import evolve,pareto_front
from deva.schema import Problem
from deva.model import Scenario,simulate
from test_core import chain
ROOT=Path(__file__).resolve().parents[1]

class AdversaryTests(unittest.TestCase):
    def test_chain_cut_and_threshold(self):
        p=Problem.parse(chain())
        cut=topology_cuts(p,[10,10])[0]
        self.assertEqual(cut['minimum_pipe_outages'],1)
        margin=critical_demand(p,[10,10],(1.,1.))
        self.assertAlmostEqual(margin['max_passing_demand_factor'],1/.95,places=5)
        result=discover(p,[10,10],max_outages=1)
        self.assertEqual(result['minimum_disturbance']['disturbance']['outage_count'],1)

    def test_demo_two_pipe_cut_and_bounded_search(self):
        raw=json.loads((ROOT/'examples/emergency_water.json').read_text());p=Problem.parse(raw)
        for cut in topology_cuts(p,[66.5,66.5,38,28.5,38,28.5]):self.assertEqual(cut['minimum_pipe_outages'],2)
        result=discover(p,[66.5,66.5,38,28.5,38,28.5],search_limit=1)
        self.assertFalse(result['enumeration_complete_within_bounds'])
        self.assertEqual(result['tested'],1)

class AuditTests(unittest.TestCase):
    def test_tampered_flow_rejected_even_with_fake_residual(self):
        p=Problem.parse(chain());s=Scenario('n',(1.,1.));r=simulate(p,[10,10],s)
        audit_result(p,[10,10],s,r)
        r['flow'][0]+=1;r['max_residual']=0
        with self.assertRaises(ValueError):audit_result(p,[10,10],s,r)

    def test_tampered_flag_and_demand_rejected(self):
        p=Problem.parse(chain());s=Scenario('n',(1.,1.));r=simulate(p,[10,10],s)
        r['passes']=False
        with self.assertRaises(ValueError):audit_result(p,[10,10],s,r)
        r=simulate(p,[10,10],s);r['demand'][-1]+=1
        with self.assertRaises(ValueError):audit_result(p,[10,10],s,r)

    def test_hash_tamper_and_graph_trace(self):
        original=json.loads((ROOT/'artifacts/emergency-water-evidence.json').read_text())
        verify_hash(original);original['science']['winner']='fake'
        with self.assertRaises(ValueError):verify_hash(original)
        graph=dict(nodes=[dict(id='a'),dict(id='b')],edges=[dict(source='a',target='b')])
        self.assertEqual(ancestors(graph,'b'),['a','b'])

class EvolutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=json.loads((ROOT/'examples/emergency_water.json').read_text())
        cls.evidence=evolve(cls.raw,77,1,8,8,8)

    def test_retained_ancestry_frontier_and_negative_results(self):
        s=self.evidence['science'];ids={c['id'] for c in s['candidates']}
        self.assertTrue(s['pareto_frontier'])
        self.assertTrue(any(c['disposition']=='rejected' for c in s['candidates']))
        self.assertTrue(any(c['generation']==1 for c in s['candidates']))
        for c in s['candidates']:
            self.assertTrue(set(c['parents'])<=ids)
            self.assertLessEqual(c['cost'],self.raw['budget']+1e-7)
            self.assertEqual(len(c['heldout']['results']),8)
        self.assertEqual(s['pareto_frontier'],pareto_front(s['candidates']))

    def test_heldout_count_does_not_affect_mutation_or_selection(self):
        other=evolve(self.raw,77,1,8,8,9)['science']
        s=self.evidence['science']
        self.assertEqual(s['recommendation'],other['recommendation'])
        self.assertEqual([c['capacities'] for c in s['candidates']],[c['capacities'] for c in other['candidates']])
        self.assertEqual(s['pareto_frontier'],other['pareto_frontier'])
        self.assertEqual(len(set(s['seeds'].values())),4)
        sets=[{r['id'] for r in ss} for ss in s['scenarios'].values()]
        for i,x in enumerate(sets):
            for y in sets[i+1:]:self.assertFalse(x&y)

    def test_exact_replay_and_provenance(self):
        other=evolve(self.raw,77,1,8,8,8)
        self.assertEqual(self.evidence['science'],other['science'])
        verify_hash(other)
        graph=other['science']['provenance'];ids={n['id'] for n in graph['nodes']}
        self.assertEqual(len(ids),len(graph['nodes']))
        self.assertTrue(all(e['source'] in ids and e['target'] in ids for e in graph['edges']))
        trace=ancestors(graph,'conclusion:recommendation')
        self.assertIn('requirement:service',trace)
        self.assertTrue(any(n.startswith('result:') for n in trace))

    def test_bad_limits_rejected(self):
        with self.assertRaises(ValueError):evolve(self.raw,generations=9)
