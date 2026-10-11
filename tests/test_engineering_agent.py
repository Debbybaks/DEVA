import json, unittest
from pathlib import Path
from deva.engineering_agent import (
    engineering_plan,
    investigate,
    counterexample_scenario,
)
from deva.hydraulic_evidence import topology_verification
from deva.audit import verify_hash

RAW = json.loads(Path("examples/emergency_water_hydraulic.json").read_text())
D = [0.125] * 6
OBJECTIVE = dict(
    component="hospital",
    maximum_failure_probability=0.02,
    maximum_cost_increase=0.12,
    training_samples=6,
    validation_samples=8,
    maximum_candidates=5,
    maximum_tool_calls=9,
    seed=20261050,
)


class EngineeringTests(unittest.TestCase):
    def test_plan_bounds_and_security(self):
        plan = engineering_plan(RAW, D, OBJECTIVE)
        self.assertEqual(plan["objective"]["component"], "hospital")
        self.assertIn("maximum_tool_calls", plan["stopping_conditions"])
        self.assertIn("registered", plan["security"])
        with self.assertRaises(ValueError):
            engineering_plan(RAW, D, dict(OBJECTIVE, code="print(1)"))
        with self.assertRaises(ValueError):
            engineering_plan(RAW, D, dict(OBJECTIVE, maximum_candidates=1000))

    def test_tool_sequence_sealed_validation_claims_and_stopping(self):
        e = investigate(RAW, D, OBJECTIVE)
        verify_hash(e)
        s = e["science"]
        self.assertFalse(
            s["target_achieved"]
        )  # Eight observations cannot establish a 2% upper probability bound.
        self.assertIn("INSUFFICIENT", s["stopping_reason"])
        tools = [r["tool"] for r in s["invocations"]]
        self.assertLess(
            tools.index("simulate_training"), tools.index("validate_selected")
        )
        self.assertEqual(len(tools), len(s["plan"]["tools"]))
        chosen = next(
            c
            for c in s["outputs"]["simulate_training"]["candidates"]
            if c["id"] == s["selection"]
        )
        self.assertLessEqual(chosen["cost"], s["plan"]["constraints"]["maximum_cost"])
        self.assertTrue(all(n["evidence"] for n in s["research_narrative"]))
        self.assertTrue(s["claim_ledger"][0]["limitations"])
        self.assertGreater(len(s["self_critique"]), 0)
        self.assertEqual(s, investigate(RAW, D, OBJECTIVE)["science"])

    def test_budget_stop_preserves_partial_outputs(self):
        s = investigate(RAW, D, dict(OBJECTIVE, maximum_tool_calls=2))["science"]
        self.assertEqual(len(s["invocations"]), 2)
        self.assertEqual(s["stopping_reason"], "COMPUTATIONAL TOOL BUDGET EXHAUSTED")
        self.assertNotIn("validate_selected", s["outputs"])
        self.assertIsNone(s["selection"])

    def test_counterexample_becomes_a_real_failure(self):
        v = topology_verification(RAW, 2)
        scenario = counterexample_scenario(RAW, v)
        self.assertEqual(set(scenario["closed"]), {"west-trunk", "east-trunk"})
        s = investigate(RAW, D, OBJECTIVE)["science"]["outputs"]["verify_property"]
        self.assertFalse(
            s["counterexample_simulation"]["records"][0]["component_passes"]
        )
        with self.assertRaises(ValueError):
            counterexample_scenario(RAW, topology_verification(RAW, 1))
