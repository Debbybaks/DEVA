"""Steady-state max-min transport and shared-capacity scenario LPs."""
from dataclasses import dataclass
import numpy as np
from scipy.optimize import linprog

TOL = 1e-7


@dataclass(frozen=True)
class Scenario:
    id: str
    availability: tuple[float, ...]
    supply_factor: float = 1.0
    demand_factor: float = 1.0

    def validate(self, p):
        if len(self.availability) != len(p.edges):
            raise ValueError('Availability dimension mismatch')
        a = np.array((*self.availability, self.supply_factor, self.demand_factor))
        if not np.isfinite(a).all() or (a < 0).any() or (a[:len(p.edges)] > 1).any():
            raise ValueError('Invalid scenario multipliers')
        if self.demand_factor <= 0 or self.demand_factor > 10 or self.supply_factor > 10:
            raise ValueError('Scenario factors outside supported bounds')


def incidence(p):
    b = np.zeros((len(p.nodes), len(p.edges)))
    for i, e in enumerate(p.edges):
        b[p.nodes.index(e.tail), i] = -1
        b[p.nodes.index(e.head), i] = 1
    return b


def operational(p, scenario):
    scenario.validate(p)
    n, m = len(p.nodes), len(p.edges)
    d = np.asarray(p.demand) * scenario.demand_factor
    s = np.asarray(p.supply) * scenario.supply_factor
    conservation = np.hstack((incidence(p), np.eye(n), -np.eye(n)))
    return n, m, d, s, conservation


def simulate(p, capacities, scenario):
    n, m, d, s, conservation = operational(p, scenario)
    c = np.asarray(capacities, dtype=float)
    if c.shape != (m,) or not np.isfinite(c).all() or (c < 0).any() or (c > np.array([e.max_capacity for e in p.edges]) + TOL).any():
        raise ValueError('Invalid design capacities')
    available = c * scenario.availability
    bounds = [(0, v) for v in np.concatenate((available, s, d))] + [(0, 1)]
    eq = np.column_stack((conservation, np.zeros(n)))
    ub = np.zeros((n, m + 2*n + 1))
    ub[:, m+n:m+2*n] = -np.eye(n)
    ub[:, -1] = d
    objective = np.zeros(m + 2*n + 1); objective[-1] = -1
    result = linprog(objective, A_ub=ub, b_ub=np.zeros(n), A_eq=eq, b_eq=np.zeros(n), bounds=bounds, method='highs')
    if not result.success:
        raise RuntimeError(f'Operational solve failed: {result.message}')
    service = float(result.x[-1])
    # Second solve maximises aggregate delivery while retaining common service.
    objective[:] = 0; objective[m+n:m+2*n] = -1
    bounds[-1] = (max(0, service - 1e-9), service)
    dispatch = linprog(objective, A_ub=ub, b_ub=np.zeros(n), A_eq=eq, b_eq=np.zeros(n), bounds=bounds, method='highs')
    if not dispatch.success:
        raise RuntimeError(f'Dispatch solve failed: {dispatch.message}')
    x = dispatch.x
    lower = np.array([v[0] for v in bounds]); upper = np.array([v[1] for v in bounds])
    residual = max(float(np.max(np.abs(eq @ x))), float(np.max(ub @ x)), float(np.max(lower-x)), float(np.max(x-upper)), 0.0)
    if residual > TOL:
        raise RuntimeError(f'Invalid numerical result: residual {residual}')
    return dict(scenario_id=scenario.id, service_fraction=service,
                flow=x[:m].tolist(), injection=x[m:m+n].tolist(),
                delivered=x[m+n:m+2*n].tolist(), demand=d.tolist(),
                max_residual=residual, passes=bool(service >= p.target-TOL))


def synthesise(p, scenarios):
    """Globally minimise continuous installation cost for a finite scenario set."""
    scenarios = tuple(scenarios)
    if not scenarios or len(scenarios) > 400:
        raise ValueError('Require 1–400 synthesis scenarios')
    m, n = len(p.edges), len(p.nodes)
    block = m + 2*n
    size = m + block * len(scenarios)
    if size * (1 + len(scenarios)*(n+m)) > 20_000_000:
        raise ValueError('Dense synthesis exceeds local memory budget; sparse worker solver required')
    costs = np.array([e.unit_cost for e in p.edges])
    objective = np.zeros(size); objective[:m] = costs
    bounds = [(0, e.max_capacity) for e in p.edges]
    equalities, inequalities, rhs = [], [], []
    budget_row = np.zeros(size); budget_row[:m] = costs
    inequalities.append(budget_row); rhs.append(p.budget)
    for index, scenario in enumerate(scenarios):
        _, _, d, s, b = operational(p, scenario)
        offset = m + index*block
        eq = np.zeros((n, size)); eq[:, offset:offset+block] = b
        equalities.extend(eq)
        for j in range(m):
            row = np.zeros(size); row[j] = -scenario.availability[j]; row[offset+j] = 1
            inequalities.append(row); rhs.append(0)
        bounds.extend([(0, None)] * m)
        bounds.extend((0, v) for v in s)
        bounds.extend((p.target*v, v) for v in d)
    result = linprog(objective, A_ub=np.array(inequalities), b_ub=np.array(rhs),
                     A_eq=np.array(equalities), b_eq=np.zeros(n*len(scenarios)), bounds=bounds, method='highs')
    if result.status == 2:
        return dict(status='infeasible', capacities=None, message=result.message)
    if not result.success:
        raise RuntimeError(f'Design solver failed: {result.message}')
    c = np.maximum(0, result.x[:m])
    if float(costs @ c) > p.budget + TOL or any(not simulate(p, c, s)['passes'] for s in scenarios):
        raise RuntimeError('Independent synthesis verification failed')
    return dict(status='optimal_within_numerical_tolerance', capacities=c.tolist(), cost=float(costs @ c), message=result.message)
