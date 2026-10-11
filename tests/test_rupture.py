import json, math, unittest
from pathlib import Path
from deva.rupture import hazard, policies, cascade, ensemble
from deva.hydraulic_evidence import audit

RAW = json.loads(Path("examples/emergency_water_hydraulic.json").read_text())
D = [0.125] * 6


class HazardTests(unittest.TestCase):
    def test_hazard_limits_and_monotonicity(self):
        p = policies(RAW)["west-trunk"]
        a = hazard(40, 0.5, p)
        b = hazard(60, 1.5, p)
        self.assertGreater(b["rate_per_second"], a["rate_per_second"])
        self.assertEqual(hazard(60, -1.5, p), b)
        with self.assertRaises(ValueError):
            hazard(40, 1, dict(p, reference_velocity_ms=0))
        with self.assertRaises(ValueError):
            hazard(40, float("nan"), p)
        self.assertFalse(hazard(None, 0, p)["pressure_known"])

    def test_seeded_cascade_states_causes_and_negative_results(self):
        p = policies(RAW)
        a = cascade(RAW, D, dict(closed=["east-trunk"]), p, seed=20261040)
        b = cascade(RAW, D, dict(closed=["east-trunk"]), p, seed=20261040)
        self.assertEqual(a, b)
        self.assertGreater(len(a["events"]), 0)
        self.assertEqual(a["frames"][0]["time_seconds"], 0)
        for frame in a["frames"]:
            audit(RAW, D, frame["scenario"], frame["result"])
            for h in frame["hazards"].values():
                self.assertAlmostEqual(
                    h["probability"],
                    -math.expm1(-h["rate_per_second"] * a["dt_seconds"]),
                )
                self.assertEqual(
                    h["hazard_change"],
                    h["rate_per_second"] - h["counterfactual_reference_rate"],
                )
        for event in a["events"]:
            self.assertLess(
                event["trigger"]["uniform_draw"], event["trigger"]["probability"]
            )
            self.assertIn("resulting_state", event)
        ids = {n["id"] for n in a["causal_graph"]["nodes"]}
        self.assertTrue(
            all(
                e["source"] in ids and e["target"] in ids and e["evidence"]
                for e in a["causal_graph"]["edges"]
            )
        )
        self.assertGreater(a["frames"][1]["hazards"]["west-trunk"]["hazard_change"], 0)

    def test_zero_hazard_and_external_repair_are_explicit(self):
        p = policies(RAW)
        for v in p.values():
            v.update(base_rate_per_second=0, stress_rate_per_second=0)
        c = cascade(
            RAW,
            D,
            dict(closed=["east-trunk", "west-trunk"]),
            p,
            steps=3,
            repairs={2: ["east-trunk"]},
        )
        self.assertEqual(
            c["frames"][1]["scenario"]["closed"], ["east-trunk", "west-trunk"]
        )
        self.assertEqual(c["frames"][2]["scenario"]["closed"], ["west-trunk"])
        self.assertEqual(c["events"][0]["event"], "EXOGENOUS REPAIR")
        self.assertTrue(all(not f.get("newly_failed", []) for f in c["frames"]))
        self.assertGreater(
            c["frames"][2]["result"]["service_fraction"],
            c["frames"][1]["result"]["service_fraction"],
        )

    def test_ensemble_reproducibility_and_percentile_order(self):
        p = policies(RAW)
        a = ensemble(RAW, D, dict(closed=["east-trunk"]), p, count=3, steps=3)
        b = ensemble(RAW, D, dict(closed=["east-trunk"]), p, count=3, steps=3)
        self.assertEqual(a, b)
        self.assertEqual(len(set(a["seeds"])), 3)
        for lo, mid, hi in zip(
            a["service_percentiles"]["5"],
            a["service_percentiles"]["50"],
            a["service_percentiles"]["95"],
        ):
            self.assertLessEqual(lo, mid)
            self.assertLessEqual(mid, hi)

    def test_reject_unknown_policy_and_unbounded_run(self):
        with self.assertRaises(ValueError):
            cascade(RAW, D, {}, {}, steps=3)
        with self.assertRaises(ValueError):
            cascade(RAW, D, {}, policies(RAW), steps=101)
        with self.assertRaises(ValueError):
            cascade(RAW, D, {}, policies(RAW), repairs={2: ["fictional"]})
