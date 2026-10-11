"""Immutable, reproducible experiment payloads with preserved negative evidence."""
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import platform
import numpy as np
import scipy
from . import MODEL_VERSION
from .schema import Problem
from .model import simulate, synthesise, Scenario
from .scenarios import declared, sampled, DISTRIBUTION
from .verification import verify, wilson


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def run(raw, seed=20261011, samples=200):
    p = Problem.parse(raw)
    # Validate sampling configuration before performing any optimisation.
    heldout = sampled(p, seed, samples)
    threats = declared(p)
    nominal = synthesise(p, threats[:1])
    robust = synthesise(p, threats)
    unit_sum = sum(e.unit_cost for e in p.edges)
    uniform = [min(e.max_capacity, p.budget/unit_sum) for e in p.edges]
    candidates = [dict(id='nominal-lp', parents=[], generation=0, synthesis=nominal),
                  dict(id='uniform', parents=[], generation=0, synthesis=dict(status='generated', capacities=uniform)),
                  dict(id='robust-lp', parents=['nominal-lp'], generation=1, synthesis=robust)]
    events = [dict(stage='UNDERSTAND', output='Validated structured problem; natural-language inference unavailable'),
              dict(stage='FORMALISE', output=MODEL_VERSION),
              dict(stage='GENERATE', output=[c['id'] for c in candidates]),
              dict(stage='OPTIMISE', output='Continuous scenario-constrained capacity-cost LP; no adaptive evolutionary search', solver='HiGHS')]
    for candidate in candidates:
        capacity = candidate['synthesis']['capacities']
        if capacity is None:
            candidate.update(disposition='rejected', reason='Scenario design LP infeasible', verification=dict(level='UNTESTED', requirements_pass=False))
            continue
        candidate['declared_results'] = [simulate(p, capacity, s) for s in threats]
        candidate['heldout_results'] = [simulate(p, capacity, s) for s in heldout]
        candidate['verification'] = verify(p, capacity, candidate['declared_results'])
        failures = sum(not r['passes'] for r in candidate['heldout_results'])
        candidate['uncertainty'] = dict(failures=failures, samples=samples, failure_rate=failures/samples,
                                       failure_rate_wilson_95=wilson(failures, samples), scope=DISTRIBUTION['caveat'])
        candidate['disposition'] = 'survives_declared_tests' if candidate['verification']['requirements_pass'] else 'rejected'
        candidate['reason'] = 'All declared requirements pass' if candidate['verification']['requirements_pass'] else 'At least one declared requirement fails'
        candidate['counterexamples'] = [r['scenario_id'] for r in candidate['declared_results']+candidate['heldout_results'] if not r['passes']]
        # Paired finite differences around nominal conditions; no probabilistic interpretation.
        base = candidate['declared_results'][0]['service_fraction']
        candidate['sensitivity'] = {
            'nominal_service': base,
            'service_change_for_1pct_demand_increase': simulate(p, capacity, Scenario('sensitivity-demand', (1.,)*len(p.edges), demand_factor=1.01))['service_fraction']-base,
            'service_change_for_1pct_supply_decrease': simulate(p, capacity, Scenario('sensitivity-supply', (1.,)*len(p.edges), supply_factor=.99))['service_fraction']-base,
            'scope':'Local one-sided finite differences, not global sensitivity indices'}
        events.append(dict(stage='SIMULATE/ATTACK/VERIFY', candidate=candidate['id'], output=candidate['verification']['level'], failures=failures))
    survivors = [c for c in candidates if c['disposition']=='survives_declared_tests']
    winner = min(survivors, key=lambda c:c['verification']['cost'])['id'] if survivors else None
    versions = dict(python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__, solver='scipy.optimize.linprog / HiGHS', method='highs')
    science = dict(schema_version='1.0', model_version=MODEL_VERSION, configuration=raw,
                   seed=seed, sample_count=samples, software=versions, distribution=DISTRIBUTION,
                   mathematical_model=dict(units='m³/h; demonstration cost currency', conservation='B f + q - y = 0', capacity='0 <= f_e <= a_e c_e', service='y_v >= target * d_v', design_objective='min sum(unit_cost_e * c_e)', reference='MATHEMATICAL_MODEL.md'),
                   assumptions=['Steady-state directed transport', 'Perfect adaptive dispatch after an event', 'Continuous capacity decisions', 'Synthetic uncalibrated hazards'],
                   scenarios=[asdict(s) for s in threats], heldout_scenarios=[asdict(s) for s in heldout],
                   candidates=candidates, winner=winner, winner_policy='Lowest cost among candidates passing all declared constraints; held-out risks reported separately',
                   provenance=events+[dict(stage='EXPLAIN', output=winner or 'No candidate survived')],
                   limitations=['No hydraulic pressure, water quality or temporal prediction', 'No formal verification', 'No real-world safety certification', 'Finite tested scenarios do not cover all hazards'])
    identifier = hashlib.sha256(canonical(science).encode()).hexdigest()
    return dict(experiment_id=f'deva-{identifier[:16]}', scientific_sha256=identifier,
                timestamp=datetime.now(timezone.utc).isoformat(), science=science)
