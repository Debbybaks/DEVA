"""Bounded rational energy-adequacy infeasibility, never AC physical proof."""

from fractions import Fraction
import hashlib


def certificate(domain, design, scenario):
    import z3

    domain.cost(design)
    for key in ["demand_factor", "solar_factor"]:
        value = scenario.get(key, 1)
        if type(value) not in (int, float) or not 0 < value <= 5:
            raise ValueError("Bounded positive operating factors required")
    if any(
        type(t) is not int or not 0 <= t < len(domain.demand)
        for t in scenario.get("generator_outages", [])
    ):
        raise ValueError("Valid outage intervals required")
    f = lambda x: Fraction(str(float(x)))
    n = len(domain.demand)
    dt = f(domain.dt) * 3600
    demand = sum(f(v) for v in domain.demand) * f(scenario.get("demand_factor", 1)) * dt
    solar = (
        sum(f(v) for v in domain.solar)
        * f(design[0])
        * f(scenario.get("solar_factor", 1))
        * dt
    )
    outages = set(scenario.get("generator_outages", []))
    generator = f(domain.generator) * 1000 * (n - len(outages)) * dt
    initial = f(design[1]) * f(domain.configuration["initial_soc"]) * f(domain.eta_d)
    upper = solar + generator + initial
    required = demand * f(domain.configuration["target"])
    context = z3.Context(proof=True)
    solver = z3.Solver(ctx=context)
    solver.set(timeout=2000)
    delivered = z3.Real("delivered_energy_J", ctx=context)
    rational = lambda v: z3.RealVal(f"{v.numerator}/{v.denominator}", ctx=context)
    solver.add(
        delivered <= rational(upper), delivered >= rational(required), delivered >= 0
    )
    result = solver.check()
    proof = solver.proof().sexpr() if result == z3.unsat else None
    return dict(
        domain="microgrid",
        requirement_id="R-ENERGY-NECESSARY",
        property="Target service requires at least target demand energy; delivered energy cannot exceed ideal available generation plus usable initial storage",
        assumptions=[
            "Finite horizon and supplied decimal parameters represented as exact rationals",
            "No unmodelled external energy source",
            "Charging losses and power limits ignored in upper bound; bound is necessary, not sufficient",
            "Perfect-foresight energy adequacy only; no AC, protection or field guarantee",
        ],
        model_version=domain.descriptor["model_version"],
        scenario=scenario,
        design=design,
        tool="Z3 " + z3.get_version_string(),
        result=str(result),
        status=(
            "FORMALLY VERIFIED BOUNDED INFEASIBILITY"
            if result == z3.unsat
            else "NECESSARY BOUND INCONCLUSIVE"
        ),
        upper_energy_J=str(upper),
        required_energy_J=str(required),
        smtlib=solver.to_smt2(),
        proof=proof,
        proof_sha256=hashlib.sha256(proof.encode()).hexdigest() if proof else None,
        scope="UNSAT certifies impossibility in this necessary-energy abstraction and hence this specified energy model. SAT is not a feasible dispatch certificate.",
    )
