"""Scope-bound empirical verification; no formal certification."""
import math
from .model import TOL


def wilson(failures, count):
    if count <= 0 or not 0 <= failures <= count:
        raise ValueError('Invalid binomial counts')
    z = 1.959963984540054
    p = failures/count; denominator = 1+z*z/count
    centre = (p+z*z/(2*count))/denominator
    half = z*math.sqrt(p*(1-p)/count+z*z/(4*count*count))/denominator
    return [max(0., centre-half), min(1., centre+half)]


def verify(p, capacities, results):
    if not results:
        return dict(level='UNTESTED', requirements_pass=False)
    cost = sum(e.unit_cost*c for e, c in zip(p.edges, capacities))
    capacity_pass = len(capacities) == len(p.edges) and all(0 <= c <= e.max_capacity+TOL for e, c in zip(p.edges, capacities))
    margins = {r['scenario_id']: min(y/d for y, d in zip(r['delivered'], r['demand']) if d > 0)-p.target for r in results}
    residuals_pass = all(r['max_residual'] <= TOL for r in results)
    passes = capacity_pass and residuals_pass and cost <= p.budget+TOL and all(v >= -TOL for v in margins.values())
    level = ('ROBUST UNDER TESTED CONDITIONS' if passes and len(results)>1 else
             'STRESS TESTED' if len(results)>1 else 'SIMULATED')
    return dict(level=level, requirements_pass=passes, cost=cost, budget_margin=p.budget-cost,
                scenario_margins=margins, scope='Declared finite capacity-network scenarios only',
                formal_verification=False, tolerance=TOL)
