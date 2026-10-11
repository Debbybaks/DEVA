"""Counterfactual failure diagnosis and common-random-number sensitivity."""
from collections import Counter
from dataclasses import replace
import numpy as np
from .model import Scenario, TOL, simulate
from .schema import Problem
from .verification import wilson


def reachable(p, capacities, scenario):
    seen = {n for n, s in zip(p.nodes, p.supply) if s * scenario.supply_factor > TOL}
    while True:
        grown = seen | {e.head for e, c, a in zip(p.edges, capacities, scenario.availability)
                        if e.tail in seen and c*a > TOL}
        if grown == seen:
            return seen
        seen = grown


def diagnose(p, capacities, scenarios, results=None):
    results = results or [simulate(p, capacities, s) for s in scenarios]
    if len(scenarios) != len(results):
        raise ValueError('Diagnosis scenario/result mismatch')
    records, counts, components, patterns = [], Counter(), Counter(), Counter()
    for scenario, result in zip(scenarios, results):
        if result['scenario_id'] != scenario.id:
            raise ValueError('Diagnosis scenario IDs must align')
        if result['passes']:
            continue
        unavailable = [e.id for e, a in zip(p.edges, scenario.availability) if a <= TOL]
        degraded = [e.id for e, a in zip(p.edges, scenario.availability) if TOL < a < 1]
        disconnected = [n for n, d in zip(p.nodes, p.demand)
                        if d > 0 and n not in reachable(p, capacities, scenario)]
        counterfactuals = {
            'restore_pipes': replace(scenario, id=scenario.id+':restore-pipes', availability=(1.,)*len(p.edges)),
            'restore_demand': replace(scenario, id=scenario.id+':restore-demand', demand_factor=1.),
            'restore_supply': replace(scenario, id=scenario.id+':restore-supply', supply_factor=1.),
            'pipes_only': Scenario(scenario.id+':pipes-only', scenario.availability),
            'demand_only': Scenario(scenario.id+':demand-only', (1.,)*len(p.edges), demand_factor=scenario.demand_factor),
            'supply_only': Scenario(scenario.id+':supply-only', (1.,)*len(p.edges), supply_factor=scenario.supply_factor),
        }
        cf = {key: simulate(p, capacities, value) for key, value in counterfactuals.items()}
        labels = []
        if disconnected:
            labels.append('topological_disconnection')
        if not cf['demand_only']['passes']:
            labels.append('demand_only_insufficiency')
        if not cf['supply_only']['passes']:
            labels.append('supply_only_insufficiency')
        if not cf['pipes_only']['passes'] and not disconnected:
            labels.append('outage_capacity_insufficiency')
        if all(cf[key]['passes'] for key in ('pipes_only', 'demand_only', 'supply_only')):
            labels.append('combined_disturbance_interaction')
        if cf['restore_demand']['passes'] and cf['restore_pipes']['passes']:
            labels.append('outage_demand_interaction')
        if not labels:
            labels.append('combined_capacity_insufficiency')
        saturated = [e.id for e,c,a,f in zip(p.edges, capacities, scenario.availability,result['flow'])
                     if c*a > TOL and abs(f-c*a) <= 1e-6]
        counts.update(labels); components.update(unavailable); patterns.update([tuple(unavailable)])
        records.append(dict(scenario_id=scenario.id, labels=labels, failed_edges=unavailable,
                            degraded_edges=degraded, disconnected_demands=disconnected,
                            saturated_edges=saturated, service_fraction=result['service_fraction'],
                            demand_factor=scenario.demand_factor, supply_factor=scenario.supply_factor,
                            counterfactuals={k:dict(service_fraction=v['service_fraction'], passes=v['passes']) for k,v in cf.items()}))
    failed = np.array([not r['passes'] for r in results], dtype=float)
    associations = {}
    for name, values in [('demand_factor', [s.demand_factor for s in scenarios]),
                         ('supply_factor', [s.supply_factor for s in scenarios]),
                         ('unavailable_count', [sum(a == 0 for a in s.availability) for s in scenarios])]:
        x = np.asarray(values, dtype=float)
        corr = float(np.corrcoef(x, failed)[0,1]) if np.std(x)>0 and np.std(failed)>0 else None
        associations[name] = dict(pearson_with_failure=corr,
                                  mean_in_failures=float(x[failed==1].mean()) if np.any(failed) else None,
                                  mean_in_passes=float(x[failed==0].mean()) if np.any(failed==0) else None,
                                  interpretation='Descriptive association; not causal or independent of other inputs')
    return dict(failures=len(records), scenario_count=len(scenarios), records=records,
                label_counts=dict(sorted(counts.items())), failed_edge_counts=dict(sorted(components.items())),
                outage_patterns=[dict(edges=list(k), failures=v) for k,v in sorted(patterns.items())],
                associations=associations, cascade='Not modelled: static transport cannot establish temporal cascading failure',
                trigger_attribution='Availability patterns do not uniquely identify independent vs corridor-triggered events',
                demand_scope='Global demand multipliers only; spatial demand patterns were not sampled')


def metrics(p, results):
    failure = np.array([not r['passes'] for r in results], dtype=float)
    unmet = np.array([sum(r['demand'])-sum(r['delivered']) for r in results])
    return dict(failure_rate=float(failure.mean()), failures=int(failure.sum()), samples=len(results),
                failure_rate_wilson_95=wilson(int(failure.sum()),len(results)), mean_unmet_m3h=float(unmet.mean()),
                mean_service=float(np.mean([r['service_fraction'] for r in results])))


def sensitivity(p, capacities, scenarios):
    """Deterministic sweeps + paired interventions over fresh IID scenarios.

    Confidence intervals are for paired mean differences, with normal asymptotics;
    clipped/discrete failures are retained, not differentiably approximated.
    """
    base_results=[simulate(p, capacities, s) for s in scenarios]
    base=metrics(p,base_results)
    base_failure=np.array([not r['passes'] for r in base_results],dtype=float)
    interventions=[]
    changes=[('demand:+5%', p, capacities, [replace(s,demand_factor=s.demand_factor*1.05) for s in scenarios]),
             ('supply:-5%', p, capacities, [replace(s,supply_factor=s.supply_factor*.95) for s in scenarios])]
    for i,e in enumerate(p.edges):
        c=list(capacities); c[i]*=.9
        changes.append((f'capacity:-10%:{e.id}',p,c,scenarios))
    for name, problem, c, ss in changes:
        results=[simulate(problem,c,s) for s in ss]
        diff=np.array([not r['passes'] for r in results],dtype=float)-base_failure
        se=float(diff.std(ddof=1)/np.sqrt(len(diff))) if len(diff)>1 else None
        interventions.append(dict(parameter=name, metrics=metrics(problem,results),
                                  failure_rate_difference=float(diff.mean()), paired_standard_error=se,
                                  paired_mean_difference_normal_95=[float(diff.mean()-1.96*se),float(diff.mean()+1.96*se)] if se is not None else None,
                                  capacity_cost=sum(e.unit_cost*x for e,x in zip(problem.edges,c))))
    sweeps=[]
    for loss in [None]+[e.id for e in p.edges]:
        a=tuple(float(e.id != loss) for e in p.edges)
        for demand in (.9,1.,1.1,1.2,1.35):
            for supply in (.75,1.):
                scenario=Scenario(f'sweep:{loss}:{demand}:{supply}',a,supply,demand)
                r=simulate(p,capacities,scenario)
                sweeps.append(dict(outage=loss,demand_factor=demand,supply_factor=supply,
                                   service_fraction=r['service_fraction'],passes=r['passes'],unmet_m3h=sum(r['demand'])-sum(r['delivered'])))
    return dict(baseline=base, paired_interventions=sorted(interventions,key=lambda x:-abs(x['failure_rate_difference'])),
                factorial_sweep=sweeps, assumptions='Common random numbers; fresh IID synthetic inputs. Paired normal intervals are asymptotic, not exact binomial intervals.',
                recovery='Untested: no storage, repairs or time dynamics in capacity model')
