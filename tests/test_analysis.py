import json
from pathlib import Path
import unittest
from deva.analysis import diagnose, sensitivity
from deva.diagnose import analyse_baseline
from deva.model import Scenario
from deva.schema import Problem
from deva.hydraulics import Pipe, solve_hydraulics
from test_core import chain

ROOT = Path(__file__).resolve().parents[1]


class DiagnosisTests(unittest.TestCase):
    def test_baseline_categories_and_hash(self):
        data = analyse_baseline(ROOT / "artifacts/emergency-water-evidence.json", 5)
        self.assertEqual(data["diagnosis"]["failures"], 38)
        self.assertEqual(
            data["source_file_sha256"],
            "14e632693c8f4b9549bb326310715f719b068da373a2feeae1c9d641378ecd5e",
        )
        counts = data["diagnosis"]["label_counts"]
        self.assertEqual(counts["topological_disconnection"], 2)
        self.assertEqual(counts["outage_demand_interaction"], 36)
        self.assertIn("Not modelled", data["diagnosis"]["cascade"])

    def test_chain_topology_and_demand_counterfactuals(self):
        p = Problem.parse(chain())
        ss = [
            Scenario("loss", (0.0, 1.0)),
            Scenario("demand", (1.0, 1.0), demand_factor=1.2),
        ]
        data = diagnose(p, [10, 10], ss)
        self.assertIn("topological_disconnection", data["records"][0]["labels"])
        self.assertIn("demand_only_insufficiency", data["records"][1]["labels"])

    def test_sensitivity_matches_analytical_sweep(self):
        p = Problem.parse(chain())
        data = sensitivity(
            p,
            [10, 10],
            [Scenario("a", (1.0, 1.0)), Scenario("b", (1.0, 1.0), demand_factor=1.1)],
        )
        row = next(
            r
            for r in data["factorial_sweep"]
            if r["outage"] is None
            and r["demand_factor"] == 1.2
            and r["supply_factor"] == 1
        )
        self.assertAlmostEqual(row["service_fraction"], 1 / 1.2)
        self.assertEqual(data["baseline"]["failures"], 1)
        self.assertTrue(
            all(
                r["metrics"]["failure_rate"] >= data["baseline"]["failure_rate"]
                for r in data["paired_interventions"]
            )
        )


class HydraulicTests(unittest.TestCase):
    def test_single_pipe_analytical_head(self):
        pipe = Pipe("p", "s", "d", 100, 0.2, 0.02)
        result = solve_hydraulics(
            ["s", "d"], [pipe], {"s": 50}, {"d": 0.01}, {"s": 0, "d": 0}
        )
        self.assertAlmostEqual(result["flow_m3s"][0], 0.01, places=8)
        self.assertAlmostEqual(
            result["head_m"]["d"], 50 - pipe.resistance * 0.01**2, places=6
        )
        self.assertTrue(result["pressure_requirement_pass"])

    def test_parallel_split(self):
        pipes = [
            Pipe("a", "s", "d", 100, 0.2, 0.02),
            Pipe("b", "s", "d", 400, 0.2, 0.02),
        ]
        result = solve_hydraulics(
            ["s", "d"], pipes, {"s": 50}, {"d": 0.03}, {"s": 0, "d": 0}
        )
        self.assertAlmostEqual(result["flow_m3s"][0], 0.02, places=7)
        self.assertAlmostEqual(result["flow_m3s"][1], 0.01, places=7)

    def test_pressure_failure_is_retained(self):
        result = solve_hydraulics(
            ["s", "d"],
            [Pipe("p", "s", "d", 100, 0.05, 0.02)],
            {"s": 20},
            {"d": 0.01},
            {"s": 0, "d": 0},
        )
        self.assertFalse(result["pressure_requirement_pass"])
        self.assertLess(result["head_m"]["d"], 0)

    def test_unanchored_component_rejected(self):
        with self.assertRaises(ValueError):
            solve_hydraulics(
                ["s", "d", "x"],
                [Pipe("p", "s", "d", 100, 0.2, 0.02)],
                {"s": 50},
                {"d": 0.01},
                {"s": 0, "d": 0, "x": 0},
            )

    def test_invalid_geometry(self):
        with self.assertRaises(ValueError):
            Pipe("a", "s", "d", 100, 0, 0.02).resistance
