"""Chronological energy adequacy, not AC power-flow or frequency simulation."""

from copy import deepcopy
import math
import numpy as np
from scipy.optimize import linprog
from ..units import si

VERSION = "microgrid-energy-lp-0.5.0"


class MicrogridDomain:
    def __init__(self, raw):
        if set(raw) != {
            "id",
            "demand",
            "solar_profile",
            "step",
            "generator",
            "charge_efficiency",
            "discharge_efficiency",
            "initial_soc",
            "target",
            "catalogues",
            "unit_costs",
        }:
            raise ValueError("Exact microgrid configuration required")
        self.configuration = deepcopy(raw)
        self.demand = np.array([si(x, "W", positive=True) for x in raw["demand"]])
        self.solar = np.asarray(raw["solar_profile"], dtype=float)
        if (
            not 2 <= len(self.demand) <= 168
            or self.solar.shape != self.demand.shape
            or not np.isfinite(self.solar).all()
            or min(self.solar) < 0
            or max(self.solar) > 1
        ):
            raise ValueError(
                "Bounded hourly profile and nonnegative solar fractions required"
            )
        self.dt = si(raw["step"], "s", positive=True) / 3600
        self.generator = si(raw["generator"], "W", positive=True) / 1000
        self.eta_c = raw["charge_efficiency"]
        self.eta_d = raw["discharge_efficiency"]
        for x in [self.eta_c, self.eta_d, raw["target"], raw["initial_soc"]]:
            if (
                isinstance(x, bool)
                or not isinstance(x, (float, int))
                or not math.isfinite(x)
                or not 0 < x <= 1
            ):
                raise ValueError("Efficiencies, SOC and target in (0,1] required")
        if set(raw["catalogues"]) != {
            "solar",
            "battery_energy",
            "battery_power",
        } or set(raw["unit_costs"]) != set(raw["catalogues"]):
            raise ValueError("Three declared catalogues and costs required")
        self.variables = []
        for name, unit in [
            ("solar", "W"),
            ("battery_energy", "J"),
            ("battery_power", "W"),
        ]:
            options = sorted({si(q, unit) for q in raw["catalogues"][name]})
            if not options or len(options) > 12 or min(options) < 0:
                raise ValueError("Bounded nonnegative construction catalogue required")
            coefficient = raw["unit_costs"][name]
            if (
                isinstance(coefficient, bool)
                or not isinstance(coefficient, (int, float))
                or not math.isfinite(coefficient)
                or coefficient < 0
            ):
                raise ValueError(
                    "Nonnegative synthetic cost per canonical unit required"
                )
            self.variables.append(dict(id=name, unit=unit, options=options))
        self.baseline = [s["options"][0] for s in self.variables]
        self.descriptor = dict(
            id="microgrid",
            model_version=VERSION,
            component_types=["solar array", "battery", "generator", "critical load"],
            state_variables=[
                dict(id="power", unit="W"),
                dict(id="stored_energy", unit="J"),
                dict(id="time", unit="s"),
            ],
            equations=[
                "solar + generator + discharge = served load + charge",
                "E[t+1] = E[t] + dt(eta_c charge - discharge/eta_d)",
            ],
            constraints=[
                "critical service each interval",
                "energy bounds",
                "converter power",
                "available generation",
                "engineering cost",
            ],
            failure_mechanisms=[
                "generator outage",
                "solar deficit",
                "demand surge",
                "storage exhaustion",
            ],
            uncertainty="Synthetic solar/demand/outage distribution, no field calibration",
            observables=["power", "SOC", "unserved energy"],
            verifiable_properties=[
                "energy conservation",
                "necessary energy-adequacy bound",
            ],
            visualisation="Chronological energy ribbon and component power paths, no water geometry",
            evidence="HiGHS LP output with independently recomputed balance audits",
            validity_envelope=dict(
                validated="Analytical outage/storage and efficiency cases",
                assumptions="Perfect-foresight dispatch, constant efficiencies, prescribed critical load",
                unvalidated="AC voltage, frequency, protection, degradation, real controls",
                calibration="Synthetic only",
                verification="Numerical linear optimisation; no formal electrical guarantee",
            ),
        )

    def cost(self, design):
        if len(design) != 3 or any(
            isinstance(x, bool)
            or not isinstance(x, (int, float))
            or not math.isfinite(x)
            or x < 0
            for x in design
        ):
            raise ValueError("Finite nonnegative SI capacities required")
        return sum(
            v * self.configuration["unit_costs"][s["id"]]
            for v, s in zip(design, self.variables)
        )

    def simulate(self, design, scenario):
        self.cost(design)
        n = len(self.demand)
        raw = self.configuration
        demand_factor = scenario.get("demand_factor", 1.0)
        solar_factor = scenario.get("solar_factor", 1.0)
        if any(
            not isinstance(v, (int, float))
            or isinstance(v, bool)
            or not math.isfinite(v)
            or v <= 0
            or v > 5
            for v in [demand_factor, solar_factor]
        ):
            raise ValueError("Operating multipliers in (0,5] required")
        outages = scenario.get("generator_outages", [])
        if not isinstance(outages, list) or any(
            type(t) is not int or not 0 <= t < n for t in outages
        ):
            raise ValueError("Outage interval indices required")
        solar_W, energy_J, power_W = design
        available = self.solar * solar_W * solar_factor / 1000
        demand = self.demand * demand_factor / 1000
        generator = np.array([0 if t in outages else self.generator for t in range(n)])
        capacity = energy_J / 3600000
        power = power_W / 1000
        # Normalised LP coordinates: kW, kWh, hours; explicit SI boundary above/below.
        # Variables [solar, generator, charge, discharge, served, E_0..E_n, z].
        size = 6 * n + 2
        z = size - 1
        eq = np.zeros((2 * n + 1, size))
        rhs = np.zeros(2 * n + 1)
        for t in range(n):
            eq[t, t] = 1
            eq[t, n + t] = 1
            eq[t, 2 * n + t] = -1
            eq[t, 3 * n + t] = 1
            eq[t, 4 * n + t] = -1
            eq[n + t, 5 * n + t] = -1
            eq[n + t, 5 * n + t + 1] = 1
            eq[n + t, 2 * n + t] = -self.dt * self.eta_c
            eq[n + t, 3 * n + t] = self.dt / self.eta_d
        eq[-1, 5 * n] = 1
        rhs[-1] = capacity * raw["initial_soc"]
        ub = np.zeros((n, size))
        for t in range(n):
            ub[t, 4 * n + t] = -1
            ub[t, z] = demand[t]
        bounds = (
            [(0, x) for x in available]
            + [(0, x) for x in generator]
            + [(0, power)] * (2 * n)
            + [(0, x) for x in demand]
            + [(0, capacity)] * (n + 1)
            + [(0, 1)]
        )
        objective = np.zeros(size)
        objective[z] = -1
        first = linprog(
            objective,
            A_eq=eq,
            b_eq=rhs,
            A_ub=ub,
            b_ub=np.zeros(n),
            bounds=bounds,
            method="highs",
        )
        if not first.success:
            raise RuntimeError(first.message)
        bounds[-1] = (first.x[z], first.x[z])
        secondary = np.zeros(size)
        secondary[n : 2 * n] = 1
        secondary[2 * n : 4 * n] = 0.001
        fit = linprog(
            secondary,
            A_eq=eq,
            b_eq=rhs,
            A_ub=ub,
            b_ub=np.zeros(n),
            bounds=bounds,
            method="highs",
        )
        if not fit.success:
            raise RuntimeError(fit.message)
        x = fit.x
        solar = x[:n] * 1000
        gen = x[n : 2 * n] * 1000
        charge = x[2 * n : 3 * n] * 1000
        discharge = x[3 * n : 4 * n] * 1000
        served = x[4 * n : 5 * n] * 1000
        energy = x[5 * n : 6 * n + 1] * 3600000
        balance = solar + gen + discharge - charge - served
        storage = np.diff(energy) - self.dt * 3600 * (
            self.eta_c * charge - discharge / self.eta_d
        )
        residual = max(
            float(np.max(np.abs(balance))), float(np.max(np.abs(storage))) / 3600
        )
        if (
            residual > 1e-5
            or min(energy) < -1e-4
            or max(energy) > energy_J + 1e-4
            or np.any(served > self.demand * demand_factor + 1e-5)
            or np.any(charge > power_W + 1e-5)
            or np.any(discharge > power_W + 1e-5)
            or np.any(solar > available * 1000 + 1e-5)
            or np.any(gen > generator * 1000 + 1e-5)
        ):
            raise ValueError("Independent microgrid conservation/bound audit failed")
        service = float(min(served / (self.demand * demand_factor)))
        energy_bound = (
            float(sum(available + generator)) * 1000 * self.dt * 3600
            + energy_J * raw["initial_soc"] * self.eta_d
        )
        required = (
            float(sum(self.demand * demand_factor)) * self.dt * 3600 * raw["target"]
        )
        return dict(
            domain="microgrid",
            model_version=VERSION,
            scenario_id=scenario["id"],
            service=service,
            passes=service >= raw["target"] - 1e-7,
            violations=[] if service >= raw["target"] - 1e-7 else ["critical_service"],
            status="NUMERICALLY VALIDATED",
            audit=dict(
                power_residual_W=float(max(abs(balance))),
                storage_residual_J=float(max(abs(storage))),
                necessary_energy_bound_J=energy_bound,
                target_energy_J=required,
            ),
            state=dict(
                time_s=[t * self.dt * 3600 for t in range(n + 1)],
                solar_W=solar.tolist(),
                generator_W=gen.tolist(),
                charge_W=charge.tolist(),
                discharge_W=discharge.tolist(),
                served_W=served.tolist(),
                demand_W=(self.demand * demand_factor).tolist(),
                energy_J=energy.tolist(),
                unserved_energy_J=float(
                    sum(self.demand * demand_factor - served) * self.dt * 3600
                ),
                solver="scipy.linprog / HiGHS, lexicographic max-min service then fuel/throughput",
                scope="Perfect foresight energy adequacy; no AC physics or physical failure cascade",
            ),
        )

    def scenarios(self, seed, count, severity=1.0):
        rng = np.random.default_rng(seed)
        n = len(self.demand)
        rows = []
        for i in range(count):
            length = (
                int(rng.integers(1, max(2, n // 2 + 1))) if rng.random() < 0.35 else 0
            )
            start = int(rng.integers(0, n - length + 1))
            rows.append(
                dict(
                    id=f"microgrid:{seed}:{i}",
                    demand_factor=float(1 + rng.uniform(0, 0.4) * severity),
                    solar_factor=float(max(0.05, 1 - rng.uniform(0, 0.8) * severity)),
                    generator_outages=list(range(start, start + length)),
                    provenance=dict(kind="SYNTHETIC IID", seed=seed, severity=severity),
                )
            )
        return rows

    def mutations(self, design, counterexample=None):
        out = []
        for i, spec in enumerate(self.variables):
            higher = [v for v in spec["options"] if v > design[i]]
            if higher:
                d = list(design)
                d[i] = min(higher)
                out.append(d)
        return out

    def verify(self, design):
        return [
            dict(
                domain="microgrid",
                property="Dispatch balance and energy constraints",
                status="NUMERICAL VALIDATION",
                assumptions=self.descriptor["validity_envelope"],
                tool="Independent balance audit",
                scope="Each solved dispatch only; no AC or formal guarantee",
            )
        ]
