import json
import math
from copy import deepcopy
from itertools import combinations
from pathlib import Path
import unittest
import z3
from deva.units import Quantity
from deva.hydraulic_v2 import simulate, parse, G, timeline
from deva.hydraulic_evidence import audit, topology_verification
from deva.hydraulic_experiment import experiment, minimal_outages

ROOT = Path(__file__).resolve().parents[1]


def quantity(value, unit):
    return {"value": value, "unit": unit}


def single(head=30, demand=0.01):
    return {
        "id": "analytical",
        "objective": "Analytical PDD",
        "nodes": [
            {"id": "s", "elevation": quantity(0, "m"), "demand": quantity(0, "m3/s")},
            {
                "id": "d",
                "elevation": quantity(0, "m"),
                "demand": quantity(demand, "m3/s"),
            },
        ],
        "pipes": [
            {
                "id": "p",
                "tail": "s",
                "head": "d",
                "length": quantity(1000, "m"),
                "friction_factor": quantity(0.02, "1"),
                "cost_per_m_at_100mm": 0.1,
                "corridor": "x",
            }
        ],
        "sources": [
            {
                "node": "s",
                "head": quantity(head, "m"),
                "maximum_supply": quantity(0.1, "m3/s"),
            }
        ],
        "target": 0.95,
        "minimum_pressure": quantity(15, "m"),
        "full_service_pressure": quantity(20, "m"),
        "maximum_velocity": quantity(3, "m/s"),
        "budget": 10000,
        "diameter_options": [quantity(0.1, "m"), quantity(0.2, "m")],
    }


class UnitTests(unittest.TestCase):
    def test_si_conversion_and_incompatible_dimensions(self):
        self.assertAlmostEqual(Quantity.of(36, "m3/h").to("L/s"), 10)
        with self.assertRaises(ValueError):
            Quantity.of(1, "Pa").to("m")
        with self.assertRaises(ValueError):
            Quantity.of(1, "m") + Quantity.of(1, "s")
        with self.assertRaises(ValueError):
            Quantity.of(True, "m")

    def test_darcy_and_pressure_dimensions(self):
        resistance = Quantity.of(100, "m") / (
            Quantity.of(G, "m/s2")
            * Quantity.of(0.1, "m")
            * Quantity.of(0.1, "m")
            * Quantity.of(0.1, "m")
            * Quantity.of(0.1, "m")
            * Quantity.of(0.1, "m")
        )
        loss = resistance * Quantity.of(0.01, "m3/s") * Quantity.of(0.01, "m3/s")
        self.assertEqual(loss.dimension, (1, 0, 0))
        pressure = (
            Quantity.of(1000, "kg/m3") * Quantity.of(G, "m/s2") * Quantity.of(10, "m")
        )
        self.assertAlmostEqual(pressure.to("Pa"), 98066.5)

    def test_parser_rejects_unit_mismatch_and_nonfinite(self):
        r = single()
        r["nodes"][1]["demand"] = quantity(40, "m")
        with self.assertRaises(ValueError):
            parse(r)
        r = single()
        r["sources"][0]["head"] = quantity(float("nan"), "m")
        with self.assertRaises(ValueError):
            parse(r)


class PDDTests(unittest.TestCase):
    def test_partial_service_closed_form(self):
        raw = single(head=20)
        r = simulate(raw, [0.1])
        resistance = 8 * 0.02 * 1000 / (G * math.pi**2 * 0.1**5)
        expected_pressure = 20 / (1 + resistance * 0.01**2 / 20)
        self.assertAlmostEqual(r["pressure_head_m"]["d"], expected_pressure, places=6)
        self.assertAlmostEqual(
            r["delivered_m3s"]["d"], 0.01 * math.sqrt(expected_pressure / 20), places=8
        )
        self.assertFalse(r["passes"])
        self.assertEqual(audit(raw, [0.1], {}, r)["result"], "pass")

    def test_full_service_analytical_and_zero_head(self):
        r = simulate(single(head=50), [0.2])
        resistance = 8 * 0.02 * 1000 / (G * math.pi**2 * 0.2**5)
        self.assertAlmostEqual(r["head_m"]["d"], 50 - resistance * 0.01**2, places=6)
        r = simulate(single(head=0), [0.1])
        self.assertLess(r["delivered_m3s"]["d"], 1e-8)

    def test_parallel_pdd_analytical_equivalent_resistance(self):
        raw = single(head=20)
        raw["pipes"].append(
            {**raw["pipes"][0], "id": "p2", "length": quantity(4000, "m")}
        )
        r = simulate(raw, [0.1, 0.1])
        self.assertAlmostEqual(r["flow_m3s"][0] / r["flow_m3s"][1], 2.0, places=6)
        resistance = 8 * 0.02 * 1000 / (G * math.pi**2 * 0.1**5) / (1 + 1 / 2) ** 2
        self.assertAlmostEqual(
            r["head_m"]["d"], 20 / (1 + resistance * 0.01**2 / 20), places=6
        )

    def test_reverse_flow_between_fixed_head_boundaries(self):
        raw = single()
        raw["nodes"][1]["demand"] = quantity(0, "m3/s")
        raw["nodes"].append(
            {
                "id": "x",
                "elevation": quantity(0, "m"),
                "demand": quantity(0.001, "m3/s"),
            }
        )
        raw["pipes"].append(
            {**raw["pipes"][0], "id": "xpipe", "tail": "d", "head": "x"}
        )
        raw["sources"].append(
            {
                "node": "d",
                "head": quantity(40, "m"),
                "maximum_supply": quantity(0.1, "m3/s"),
            }
        )
        r = simulate(raw, [0.2, 0.2])
        expected = -math.sqrt(10 / (8 * 0.02 * 1000 / (G * math.pi**2 * 0.2**5)))
        self.assertAlmostEqual(r["flow_m3s"][0], expected, places=8)
        self.assertFalse(r["requirements"]["source_supply"])

    def test_outage_and_source_loss_unknown_pressure(self):
        raw = single()
        r = simulate(raw, [0.1], {"closed": ["p"]})
        self.assertIsNone(r["pressure_head_m"]["d"])
        self.assertEqual(r["service_fraction"], 0)
        audit(raw, [0.1], {"closed": ["p"]}, r)
        r = simulate(raw, [0.1], {"source_losses": ["s"]})
        self.assertTrue(all(h is None for h in r["head_m"].values()))

    def test_supply_velocity_and_tamper_checked(self):
        raw = single(head=50)
        raw["sources"][0]["maximum_supply"] = quantity(0.001, "m3/s")
        r = simulate(raw, [0.2])
        self.assertFalse(r["requirements"]["source_supply"])
        c = deepcopy(r)
        c["flow_m3s"][0] += 0.001
        with self.assertRaises(ValueError):
            audit(raw, [0.2], {}, c)
        c = deepcopy(r)
        c["passes"] = True
        with self.assertRaises(ValueError):
            audit(raw, [0.2], {}, c)
        c = deepcopy(r)
        c["head_m"]["d"] = None
        with self.assertRaises(ValueError):
            audit(raw, [0.2], {}, c)

    def test_discrete_diameter_values_do_not_force_monotone_safety(self):
        raw = json.loads((ROOT / "examples/emergency_water_hydraulic.json").read_text())
        a = simulate(raw, [0.125] * 6)
        b = simulate(raw, [0.2] * 6)
        self.assertTrue(a["requirements"]["source_supply"])
        self.assertFalse(b["requirements"]["source_supply"])


class TemporalTests(unittest.TestCase):
    def test_variable_head_tank_closed_form_and_step_refinement(self):
        raw = single(head=20)
        tank = dict(
            node="s",
            area=quantity(10, "m2"),
            initial_volume=quantity(100, "m3"),
            maximum_volume=quantity(200, "m3"),
            base_head=quantity(0, "m"),
            inflow=quantity(0, "m3/s"),
        )
        resistance = 8 * 0.02 * 1000 / (G * math.pi**2 * 0.1**5)
        k = 0.01 / math.sqrt(20 + resistance * 0.01**2)
        exact = 10 * (math.sqrt(10) - k * 1000 / 20) ** 2
        a = timeline(raw, [0.1], tank, 10, 100)["frames"][-1]["volume_m3"]
        b = timeline(raw, [0.1], tank, 20, 50)["frames"][-1]["volume_m3"]
        self.assertLess(abs(b - exact), abs(a - exact) * 0.6)
        self.assertLess(abs(b - exact), 0.01)

    def test_analytical_tank_balance_and_events(self):
        raw = single(head=50)
        tank = {
            "node": "s",
            "area": quantity(10, "m2"),
            "initial_volume": quantity(10, "m3"),
            "maximum_volume": quantity(20, "m3"),
            "base_head": quantity(50, "m"),
            "inflow": quantity(0.005, "m3/s"),
        }
        r = timeline(
            raw, [0.2], tank, 4, 100, [{"step": 2, "scenario": {"closed": ["p"]}}]
        )
        self.assertAlmostEqual(r["frames"][2]["volume_m3"], 9, places=6)
        self.assertAlmostEqual(r["frames"][4]["volume_m3"], 10, places=6)
        self.assertLess(r["volume_balance_error_m3"], 1e-10)
        self.assertEqual(r["frames"][2]["result"]["service_fraction"], 0)

    def test_empty_tank_event_shortens_step_without_negative_volume(self):
        raw = single(head=50)
        tank = {
            "node": "s",
            "area": quantity(10, "m2"),
            "initial_volume": quantity(0.1, "m3"),
            "maximum_volume": quantity(20, "m3"),
            "base_head": quantity(50, "m"),
            "inflow": quantity(0, "m3/s"),
        }
        r = timeline(raw, [0.2], tank, 3, 100)
        self.assertAlmostEqual(r["frames"][1]["time_seconds"], 10, places=4)
        self.assertIn("tank_empty", r["frames"][1]["events"])
        self.assertEqual(r["frames"][1]["result"]["service_fraction"], 0)


class FormalTests(unittest.TestCase):
    def test_bounded_topology_proof_and_replayed_smt(self):
        raw = json.loads((ROOT / "examples/emergency_water_hydraulic.json").read_text())
        r = topology_verification(raw, 1)
        self.assertEqual(r["result"], "unsat")
        self.assertTrue(r["proof"])
        s = z3.Solver()
        s.from_string(r["smtlib"])
        self.assertEqual(str(s.check()), "unsat")
        r = topology_verification(raw, 2)
        self.assertEqual(r["result"], "sat")
        self.assertEqual(len(r["counterexample_closed"]), 2)
        state = simulate(raw, [0.125] * 6, {"closed": r["counterexample_closed"]})
        self.assertFalse(state["passes"])

    def test_encoding_matches_exhaustive_connectivity(self):
        raw = json.loads((ROOT / "examples/emergency_water_hydraulic.json").read_text())
        m = parse(raw)
        for k in [0, 1, 2]:
            disconnected = any(
                bool(
                    simulate(raw, [0.125] * 6, {"closed": list(c)})[
                        "disconnected_nodes"
                    ]
                )
                for c in combinations([e["id"] for e in m["pipes"]], k)
            )
            self.assertEqual(
                topology_verification(raw, k)["result"] == "sat", disconnected
            )


class CoupledPipelineTests(unittest.TestCase):
    def test_infeasible_budget_keeps_negative_candidates_without_opening_test(self):
        raw = single()
        raw["budget"] = 1
        r = experiment(raw, 8, 1, 3, 3, 3)
        self.assertIsNone(r["science"]["recommendation"])
        self.assertEqual(len(r["science"]["candidates"]), 2)
        self.assertNotIn("heldout", r["science"]["scenarios"])

    def test_replay_separation_ancestry_and_claim_scope(self):
        raw = json.loads((ROOT / "examples/emergency_water_hydraulic.json").read_text())
        a = experiment(raw, 7, 1, 3, 3, 4)
        b = experiment(raw, 7, 1, 3, 3, 5)
        self.assertEqual(a["science"]["recommendation"], b["science"]["recommendation"])
        self.assertEqual(
            [c["diameters_m"] for c in a["science"]["candidates"]],
            [c["diameters_m"] for c in b["science"]["candidates"]],
        )
        self.assertEqual(a["science"]["seeds"], b["science"]["seeds"])
        self.assertTrue(any(c["parents"] for c in a["science"]["candidates"]))
        self.assertTrue(
            all(
                c["verification_status"] == "STRESS TESTED"
                for c in a["science"]["candidates"]
            )
        )
        self.assertEqual(len(a["science"]["claim_ledger"]), 3)
        c = experiment(raw, 7, 1, 3, 3, 4)
        self.assertEqual(a["science"], c["science"])

    def test_minimal_outage_set_with_controlled_counterfactuals(self):
        raw = json.loads((ROOT / "examples/emergency_water_hydraulic.json").read_text())
        r = minimal_outages(
            raw, [0.125] * 6, {"closed": ["west-trunk", "east-trunk", "west-hospital"]}
        )
        self.assertTrue(r["one_minimal"])
        self.assertEqual(len(r["minimized"]["closed"]), 2)


if __name__ == "__main__":
    unittest.main()


class CascadeTests(unittest.TestCase):
    def test_state_driven_isolation_and_termination(self):
        from deva.cascade import protective_cascade

        raw = json.loads((ROOT / "examples/emergency_water_hydraulic.json").read_text())
        r = protective_cascade(
            raw,
            [0.125] * 6,
            {"closed": ["east-trunk"]},
            {"west-trunk": quantity(0.5, "m/s")},
        )
        self.assertEqual(r["rounds"][0]["newly_closed"], ["west-trunk"])
        self.assertEqual(r["rounds"][1]["result"]["service_fraction"], 0)
        self.assertLessEqual(len(r["rounds"]), 7)
        self.assertEqual(
            r["rounds"][0]["causes"][0]["rule"],
            "abs(velocity) > explicit excess-flow setpoint",
        )
