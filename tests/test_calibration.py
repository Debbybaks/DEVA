import json
from pathlib import Path
import unittest
import numpy as np
from copy import deepcopy
from deva.calibration import (
    observations,
    parameters,
    apply,
    predict,
    jacobian,
    identifiability,
    calibrate,
    sensor_placement,
)
from deva.digital_twin import benchmark_data, twin_states

RAW = json.loads(Path("examples/emergency_water_hydraulic.json").read_text())
D = [0.125] * 6


class CalibrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = benchmark_data(RAW, D, 20261030)
        cls.fit = calibrate(
            RAW,
            D,
            cls.data["parameters"],
            cls.data["splits"]["calibration"],
            cls.data["splits"]["validation"],
            starts=1,
        )

    def test_observation_units_and_provenance(self):
        r = deepcopy(self.data["splits"]["calibration"])
        r[0]["measurement"]["unit"] = "m3/s"
        with self.assertRaises(ValueError):
            observations(RAW, r)
        r = deepcopy(self.data["splits"]["calibration"])
        r[0]["uncertainty"]["value"] = 0
        with self.assertRaises(ValueError):
            observations(RAW, r)
        r = deepcopy(self.data["splits"]["calibration"])
        r[0]["timestamp"] = "2026-10-01"
        with self.assertRaises(ValueError):
            observations(RAW, r)
        with self.assertRaises(ValueError):
            observations(RAW, [r[1], r[1]])

    def test_overlap_and_parameter_domains(self):
        with self.assertRaises(ValueError):
            calibrate(
                RAW,
                D,
                self.data["parameters"],
                self.data["splits"]["calibration"],
                self.data["splits"]["calibration"],
            )
        with self.assertRaises(ValueError):
            apply(RAW, self.data["parameters"], [100, 1, 1])
        p = deepcopy(self.data["parameters"])
        p[1]["components"] = p[0]["components"]
        with self.assertRaises(ValueError):
            parameters(RAW, p)

    def test_hidden_parameter_recovery_and_heldout(self):
        self.assertEqual(self.fit["status"], "BENCHMARK CALIBRATED")
        for fitted, truth in zip(self.fit["parameters"], self.data["ground_truth"]):
            self.assertLess(abs(fitted["estimate"] - truth) / truth, 0.04)
        metrics = self.fit["metrics"]["validation"]
        self.assertLess(metrics["weighted_rmse"], 2)
        self.assertLess(metrics["weighted_rmse"], metrics["initial_weighted_rmse"])
        self.assertTrue(self.fit["fitted_identifiability"]["locally_identifiable"])
        self.assertIsNotNone(self.fit["covariance"])

    def test_insufficient_observations_expose_rank_deficiency(self):
        train = self.data["splits"]["calibration"][:1]
        r = calibrate(
            RAW,
            D,
            self.data["parameters"],
            train,
            self.data["splits"]["validation"],
            starts=1,
        )
        self.assertEqual(r["fitted_identifiability"]["rank"], 1)
        self.assertEqual(r["status"], "INSUFFICIENT CALIBRATION EVIDENCE")
        self.assertIsNone(r["covariance"])
        self.assertTrue(all(p["standard_error"] is None for p in r["parameters"]))

    def test_noiseless_forward_recovery_and_sign(self):
        data = benchmark_data(RAW, D, 20261031, noise=False)
        records = observations(RAW, data["splits"]["calibration"])
        np.testing.assert_allclose(
            predict(RAW, D, data["parameters"], data["ground_truth"], records),
            [r["value_si"] for r in records],
            atol=1e-12,
        )
        fitted = calibrate(
            RAW,
            D,
            data["parameters"],
            data["splits"]["calibration"],
            data["splits"]["validation"],
            starts=1,
        )
        np.testing.assert_allclose(
            [p["estimate"] for p in fitted["parameters"]],
            data["ground_truth"],
            atol=1e-5,
        )

    def test_validation_cannot_change_fitted_parameters(self):
        invalid = deepcopy(self.data["splits"]["validation"])
        for r in invalid:
            r["measurement"]["value"] += 100 * r["uncertainty"]["value"]
        bad = calibrate(
            RAW,
            D,
            self.data["parameters"],
            self.data["splits"]["calibration"],
            invalid,
            starts=1,
        )
        self.assertEqual(
            [p["estimate"] for p in bad["parameters"]],
            [p["estimate"] for p in self.fit["parameters"]],
        )
        self.assertEqual(bad["status"], "INSUFFICIENT CALIBRATION EVIDENCE")

    def test_sensor_design_is_exhaustive_and_measurement_weighted(self):
        result = sensor_placement(
            RAW,
            D,
            self.data["parameters"],
            self.data["ground_truth"],
            self.data["splits"]["calibration"],
            budget=2,
        )
        self.assertEqual(len(result["layouts"]), 6)
        self.assertEqual(len(result["recommendation"]), 2)
        self.assertGreaterEqual(
            result["layouts"][0]["information_score"],
            result["layouts"][-1]["information_score"],
        )
        weak = deepcopy(self.data["splits"]["calibration"])
        for r in weak:
            r["uncertainty"]["value"] *= 10
        other = sensor_placement(
            RAW, D, self.data["parameters"], self.data["ground_truth"], weak, budget=2
        )
        self.assertLess(
            other["layouts"][0]["information_score"],
            result["layouts"][0]["information_score"],
        )

    def test_digital_twin_categories_and_reproducible_observations(self):
        self.assertEqual(self.data, benchmark_data(RAW, D, 20261030))
        self.assertNotEqual(
            self.data["splits"], benchmark_data(RAW, D, 20261031)["splits"]
        )
        twin = twin_states(RAW, D, self.fit)
        categories = {s["category"] for s in twin["states"]}
        self.assertTrue(
            {"OBSERVED", "ESTIMATED", "FORECAST", "SIMULATED"} <= categories
        )
        observed = [s for s in twin["states"] if s["category"] == "OBSERVED"]
        self.assertTrue(all(s["provenance"]["kind"] == "SYNTHETIC" for s in observed))
        self.assertTrue(all(s["provenance"] for s in twin["states"]))

    def test_conditional_value_of_information_records_existing_sensors(self):
        r = sensor_placement(
            RAW,
            D,
            self.data["parameters"],
            self.data["ground_truth"],
            self.data["splits"]["calibration"],
            budget=1,
            current_sensors=["west-meter"],
        )
        self.assertEqual(len(r["layouts"]), 3)
        self.assertTrue(
            all(
                "west-meter" in layout["sensors"] and len(layout["added_sensors"]) == 1
                for layout in r["layouts"]
            )
        )
        self.assertTrue(
            all(
                v["information_gain"] >= 0 and v["sensor"] != "west-meter"
                for v in r["value_of_information"]
            )
        )
        with self.assertRaises(ValueError):
            sensor_placement(
                RAW,
                D,
                self.data["parameters"],
                self.data["ground_truth"],
                self.data["splits"]["calibration"],
                current_sensors=["unknown"],
            )

    def test_analytical_source_head_offset_and_observation_conversion(self):
        spec = [
            dict(
                id="west-head-offset",
                kind="source_head_offset",
                components=["source-west"],
                initial=0.0,
                lower=-4.0,
                upper=4.0,
            )
        ]
        r = dict(
            id="source:cal",
            timestamp="2026-10-01T00:00:00Z",
            sensor_id="west-pressure",
            component="source-west",
            measurement_type="pressure",
            measurement=dict(value=48000.0, unit="mm"),
            uncertainty=dict(value=100.0, unit="mm"),
            scenario=dict(id="source:known-head"),
            provenance=dict(kind="SYNTHETIC", source="analytical fixed-head boundary"),
        )
        validation = deepcopy(r)
        validation["id"] = "source:validation"
        validation["timestamp"] = "2026-10-02T00:00:00Z"
        fit = calibrate(RAW, D, spec, [r], [validation], starts=1)
        self.assertAlmostEqual(fit["parameters"][0]["estimate"], 3.0, places=6)
        self.assertEqual(fit["parameters"][0]["unit"], "m")
        self.assertAlmostEqual(fit["parameters"][0]["standard_error"], 0.1, places=5)
        self.assertEqual(fit["status"], "BENCHMARK CALIBRATED")
