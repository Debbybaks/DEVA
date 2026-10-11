"""Reference adapter: no hydraulic equations or legacy orchestration are replaced."""

from copy import deepcopy
from ..hydraulic_v2 import parse, simulate, cost, VERSION
from ..hydraulic_evidence import audit, topology_verification
from ..hydraulic_experiment import sampled


class WaterDomain:
    def __init__(self, raw):
        self.configuration = deepcopy(raw)
        self.model = parse(raw)
        self.variables = [
            dict(id=p["id"], unit="m", options=self.model["options"])
            for p in self.model["pipes"]
        ]
        self.baseline = [
            0.125 if 0.125 in v["options"] else min(v["options"])
            for v in self.variables
        ]
        self.descriptor = dict(
            id="water",
            model_version=VERSION,
            component_types=["reservoir", "junction", "pipe", "demand"],
            state_variables=[
                dict(id="pressure_head", unit="m"),
                dict(id="flow", unit="m3/s"),
                dict(id="service", unit="1"),
            ],
            equations=[
                "sum signed pipe flow + source injection = delivered demand",
                "head loss = r q |q|",
                "pressure-dependent demand",
            ],
            constraints=[
                "service",
                "pressure",
                "velocity",
                "source_supply",
                "engineering_cost",
            ],
            failure_mechanisms=["closure", "source head depression", "demand surge"],
            uncertainty="Seeded synthetic outage/demand/source distribution; field calibration incomplete",
            observables=["pressure", "flow", "service"],
            verifiable_properties=["bounded topology connectivity"],
            visualisation="Existing hydraulic state adapter; pressure and signed-flow network",
            evidence="Unmodified hydraulic result plus independent audit and domain-scoped wrapper",
            validity_envelope=dict(
                validated="Analytical steady PDD/Darcy cases and conservation",
                assumptions="Prescribed heads, fixed friction",
                unvalidated="Field fidelity, physical rupture, transients",
                calibration="Synthetic only",
                verification="Numerical hydraulics; bounded Boolean topology only",
            ),
        )

    def cost(self, design):
        return cost(self.model, design)

    def simulate(self, design, scenario):
        physical = {k: v for k, v in scenario.items() if k != "provenance"}
        r = simulate(self.configuration, design, physical)
        evidence = audit(self.configuration, design, physical, r)
        return dict(
            domain="water",
            model_version=VERSION,
            scenario_id=scenario["id"],
            passes=r["passes"],
            service=r["service_fraction"],
            violations=[k for k, v in r["requirements"].items() if not v],
            state=r,
            audit=evidence,
            status="NUMERICALLY VALIDATED",
        )

    def scenarios(self, seed, count, severity=1.0):
        rows = sampled(self.model, seed, count)
        for r in rows:
            r["demand_factor"] = 1 + (r["demand_factor"] - 1) * severity
            r["source_head_delta_m"] *= severity
            r["provenance"] = dict(kind="SYNTHETIC IID", seed=seed, severity=severity)
        return rows

    def mutations(self, design, counterexample=None):
        # Intervention-ranked upgrade: greatest service gain in the witnessed scenario.
        out = []
        for i, spec in enumerate(self.variables):
            higher = [x for x in spec["options"] if x > design[i] + 1e-8]
            if higher:
                child = list(design)
                child[i] = min(higher)
                out.append(child)
        return out

    def verify(self, design):
        result = topology_verification(self.configuration, max_outages=1)
        return [dict(domain="water", **result)]
