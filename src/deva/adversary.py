"""Bounded active search for counterexamples, not an IID reliability estimator."""

from dataclasses import asdict
from itertools import combinations
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import maximum_flow
from .analysis import reachable
from .model import Scenario, TOL, simulate


def topology_cuts(p, capacities):
    """Exact integer unit-edge min cuts: disconnect one demand from all sources.

    Ignore edges of zero installed capacity. Capacities count pipes, not m³/h.
    Parallel edges accumulate; returned edge witness checks reachability.
    """
    n = len(p.nodes)
    super_source = n
    matrix = np.zeros((n + 1, n + 1), dtype=np.int64)
    for e, c in zip(p.edges, capacities):
        if c > TOL:
            matrix[p.nodes.index(e.tail), p.nodes.index(e.head)] += 1
    for i, s in enumerate(p.supply):
        if s > 0:
            matrix[super_source, i] = len(p.edges) + 1
    output = []
    for node, d in zip(p.nodes, p.demand):
        if d <= 0:
            continue
        if p.supply[p.nodes.index(node)] > 0:
            output.append(
                dict(
                    demand_node=node,
                    minimum_pipe_outages=None,
                    edges=[],
                    scope="Demand co-located with source; pipe deletion cannot remove local source connectivity",
                )
            )
            continue
        flow = maximum_flow(csr_matrix(matrix), super_source, p.nodes.index(node))
        residual = matrix - flow.flow.toarray()
        seen = {super_source}
        while True:
            grown = seen | {j for i in seen for j in range(n + 1) if residual[i, j] > 0}
            if grown == seen:
                break
            seen = grown
        cut = [
            e.id
            for e, c in zip(p.edges, capacities)
            if c > TOL
            and p.nodes.index(e.tail) in seen
            and p.nodes.index(e.head) not in seen
        ]
        a = tuple(float(e.id not in cut) for e in p.edges)
        if node in reachable(p, capacities, Scenario("cut-check", a)):
            raise RuntimeError("Min-cut witness failed independent reachability check")
        output.append(
            dict(
                demand_node=node,
                minimum_pipe_outages=int(flow.flow_value),
                edges=cut,
                scope="Unit-edge topology cut; ignores pressure and capacity sufficiency",
            )
        )
    return output


def critical_demand(
    p, capacities, availability, supply_factor=1.0, upper=2.0, iterations=28
):
    def evaluate(value):
        return simulate(
            p, capacities, Scenario("margin", tuple(availability), supply_factor, value)
        )

    lower = 0.1
    if not evaluate(lower)["passes"]:
        return dict(
            max_passing_demand_factor=None,
            first_failing_demand_factor=lower,
            status="Fails at lower search bound",
        )
    if evaluate(upper)["passes"]:
        return dict(
            max_passing_demand_factor=upper,
            first_failing_demand_factor=None,
            status="No failure within search bound",
        )
    for _ in range(iterations):
        mid = (lower + upper) / 2
        if evaluate(mid)["passes"]:
            lower = mid
        else:
            upper = mid
    return dict(
        max_passing_demand_factor=lower,
        first_failing_demand_factor=upper,
        status="Numerically bracketed monotone threshold",
    )


def discover(p, capacities, max_outages=2, search_limit=500):
    if not 1 <= max_outages <= 3 or not 1 <= search_limit <= 2000:
        raise ValueError("Invalid adversary search bounds")
    records = []
    tested = 0
    complete = True
    for size in range(1, min(max_outages, len(p.edges)) + 1):
        for combo in combinations(range(len(p.edges)), size):
            for demand, supply in ((1.0, 1.0), (1.35, 1.0), (1.35, 0.75)):
                if tested >= search_limit:
                    complete = False
                    break
                a = tuple(float(i not in combo) for i in range(len(p.edges)))
                scenario = Scenario(f"adversary:{tested:04d}", a, supply, demand)
                result = simulate(p, capacities, scenario)
                tested += 1
                records.append(
                    dict(
                        scenario=asdict(scenario),
                        result=result,
                        disturbance=dict(
                            outage_count=size,
                            demand_increase=demand - 1,
                            supply_loss=1 - supply,
                        ),
                    )
                )
            if not complete:
                break
        if not complete:
            break
    failures = [r for r in records if not r["result"]["passes"]]
    # Lexicographic objective is explicit, not described as calibrated plausibility.
    minimum = (
        min(
            failures,
            key=lambda r: (
                r["disturbance"]["outage_count"],
                r["disturbance"]["demand_increase"] + r["disturbance"]["supply_loss"],
                r["result"]["service_fraction"],
            ),
        )
        if failures
        else None
    )
    margins = []
    for i, e in enumerate(p.edges):
        a = tuple(float(j != i) for j in range(len(p.edges)))
        margins.append(dict(edge=e.id, **critical_demand(p, capacities, a)))
    return dict(
        search_family="Enumerated pipe outages crossed with declared demand/supply corners",
        tested=tested,
        max_outages=max_outages,
        search_limit=search_limit,
        enumeration_complete_within_bounds=complete,
        results=records,
        failures=len(failures),
        minimum_disturbance=minimum,
        ranking_policy="Fewest outages, then smallest demand-increase + supply-loss, then lowest service in finite family",
        topology_cuts=topology_cuts(p, capacities),
        single_outage_demand_margins=margins,
        caveat="Active adversarial results are deliberately selected; no binomial failure probability attached",
    )
