import unittest
from pathlib import Path
from deva.remaining import analyse, augmentation
from deva.schema import Problem
from deva.model import Scenario
from test_core import chain

ROOT = Path(__file__).resolve().parents[1]


class RemainingTests(unittest.TestCase):
    def test_sealed_thirteen_and_only_three_bounded_repairs(self):
        r = analyse(ROOT / "artifacts/evolution-evidence.json")
        self.assertEqual(r["diagnosis"]["failures"], 13)
        self.assertEqual(r["diagnosis"]["label_counts"]["topological_disconnection"], 6)
        self.assertEqual(
            sum(x["additional_cost"] is not None for x in r["posthoc_repairs"]), 3
        )
        self.assertIn("Sealed test set opened for diagnosis only", r["scope"])

    def test_analytical_augmentation_cost_and_no_pipe_only_disconnection_repair(self):
        p = Problem.parse(chain())
        r = augmentation(p, [8.0, 8.0], Scenario("need", (1.0, 1.0)))
        self.assertAlmostEqual(
            r["additional_cost"], 3.0
        )  # Two unit-cost pipes each require +1.5 at target 0.95
        self.assertIsNone(
            augmentation(p, [8.0, 8.0], Scenario("cut", (0.0, 1.0)))["additional_cost"]
        )
