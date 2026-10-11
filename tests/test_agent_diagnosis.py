import json
from pathlib import Path
import unittest

from deva.agent_diagnosis import diagnose


class AgentDiagnosisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.package = json.loads(
            (
                Path(__file__).resolve().parents[1]
                / "artifacts/digital-twin-evidence.json"
            ).read_text()
        )
        cls.result = diagnose(cls.package)

    def test_preserved_failures_and_conditional_mechanism(self):
        s = self.result["science"]
        self.assertEqual((s["failures"], s["samples"], len(s["cases"])), (4, 40, 4))
        for case in s["cases"]:
            self.assertEqual(case["replay"]["state"], case["original_record"]["result"])
            self.assertEqual(
                case["mechanism"], "CONNECTED HYDRAULIC SERVICE/PRESSURE DEFICIT"
            )
            self.assertTrue(case["counterfactuals"]["remove_outages"]["passes"])
            self.assertFalse(
                case["counterfactuals"]["nominal_demand_and_head"]["passes"]
            )
            self.assertFalse(case["single_outage_probes"]["east-trunk"]["passes"])

    def test_diagnostic_cost_retains_negative_alternatives(self):
        probes = self.result["science"]["diagnostic_design_probes"]
        self.assertTrue(any(p["resolved_observed_failures"] == 0 for p in probes))
        west = next(
            p
            for p in probes
            if p["pipe"] == "west-trunk" and abs(p["diameter_after_m"] - 0.175) < 1e-8
        )
        self.assertEqual(west["resolved_observed_failures"], 4)
        self.assertAlmostEqual(west["cost_delta"], 55.04939467464891)
        self.assertIn("No new reliability claim", self.result["science"]["scope"])

    def test_tampered_evidence_rejected(self):
        package = dict(self.package, scientific_sha256="0" * 64)
        with self.assertRaises(ValueError):
            diagnose(package)


if __name__ == "__main__":
    unittest.main()
