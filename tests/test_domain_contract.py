import json
from pathlib import Path
import unittest
from copy import deepcopy
from deva.domain_contract import validate_domain, validate_outcome
from deva.domains.water import WaterDomain
from deva.domains.microgrid import MicrogridDomain
from deva.hydraulic_v2 import simulate
from deva.units import Quantity

ROOT = Path(__file__).resolve().parents[1]


class DomainTests(unittest.TestCase):
    def test_water_adapter_exact_migration(self):
        raw = json.loads((ROOT / "examples/emergency_water_hydraulic.json").read_text())
        domain = validate_domain(WaterDomain(raw))
        scenario = {"id": "migration", "closed": ["east-trunk"]}
        self.assertEqual(
            domain.simulate(domain.baseline, scenario)["state"],
            simulate(raw, domain.baseline, scenario),
        )

    def test_cross_domain_evidence_rejected(self):
        d = MicrogridDomain(json.loads((ROOT / "examples/microgrid.json").read_text()))
        with self.assertRaises(ValueError):
            validate_outcome(d, dict(domain="water", model_version="bad"))

    def test_energy_dimensions(self):
        self.assertAlmostEqual(
            (Quantity.of(2, "kW") * Quantity.of(3, "h")).to("kWh"), 6
        )
        with self.assertRaises(ValueError):
            Quantity.of(1, "W").to("J")

    def test_storage_analytical_limit_and_efficiency(self):
        raw = json.loads((ROOT / "examples/microgrid.json").read_text())
        raw.update(
            demand=[dict(value=10, unit="kW")] * 2,
            solar_profile=[0, 0],
            initial_soc=1,
            charge_efficiency=1,
            discharge_efficiency=1,
        )
        d = validate_domain(MicrogridDomain(raw))
        s = dict(id="analytical", generator_outages=[0, 1])
        r = d.simulate([0, 10 * 3600000, 10 * 1000], s)
        self.assertAlmostEqual(r["service"], 0.5)
        self.assertAlmostEqual(r["state"]["energy_J"][-1], 0)
        raw["discharge_efficiency"] = 0.8
        r = MicrogridDomain(raw).simulate([0, 10 * 3600000, 10 * 1000], s)
        self.assertAlmostEqual(r["service"], 0.4)
        self.assertLess(r["audit"]["storage_residual_J"], 1e-5)

    def test_power_limit_independent_of_energy(self):
        raw = json.loads((ROOT / "examples/microgrid.json").read_text())
        raw.update(
            demand=[dict(value=10, unit="kW")] * 2,
            solar_profile=[0, 0],
            initial_soc=1,
            discharge_efficiency=1,
        )
        r = MicrogridDomain(raw).simulate(
            [0, 100 * 3600000, 2000], dict(id="power", generator_outages=[0, 1])
        )
        self.assertAlmostEqual(r["service"], 0.2)
        self.assertGreater(r["state"]["energy_J"][-1], 0)

    def test_reproducible_outages_and_bad_units(self):
        raw = json.loads((ROOT / "examples/microgrid.json").read_text())
        d = MicrogridDomain(raw)
        self.assertEqual(d.scenarios(9, 20), d.scenarios(9, 20))
        raw["generator"]["unit"] = "m"
        with self.assertRaises(ValueError):
            MicrogridDomain(raw)

    def test_bounded_energy_infeasibility_has_replayable_proof(self):
        import z3
        from deva.domains.energy_certificate import certificate

        raw = json.loads((ROOT / "examples/microgrid.json").read_text())
        raw.update(
            demand=[dict(value=10, unit="kW")] * 2,
            solar_profile=[0, 0],
            initial_soc=1,
            discharge_efficiency=1,
        )
        c = certificate(
            MicrogridDomain(raw),
            [0, 10 * 3600000, 10000],
            dict(id="bound", generator_outages=[0, 1]),
        )
        self.assertEqual(c["result"], "unsat")
        self.assertTrue(c["proof"])
        solver = z3.Solver()
        solver.from_string(c["smtlib"])
        self.assertEqual(solver.check(), z3.unsat)
