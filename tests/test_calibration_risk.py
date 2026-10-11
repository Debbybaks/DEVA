from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unittest

import numpy as np

from deva.calibration_risk import propagate
from deva.experiment import canonical


class CalibrationRiskTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.package = json.loads(
            (
                Path(__file__).resolve().parents[1]
                / "artifacts/digital-twin-evidence.json"
            ).read_text()
        )

    def test_shared_parameter_draws_are_exactly_reproducible(self):
        first = propagate(self.package, samples=4, seed=17)
        self.assertEqual(first, propagate(self.package, samples=4, seed=17))
        self.assertEqual(len(first["science"]["draws"]), 4)
        self.assertEqual(len(first["science"]["cases"]), 4)
        for c in first["science"]["cases"]:
            self.assertEqual((c["failure_count"], c["unknown_states"]), (4, 0))
            self.assertEqual(
                sorted(c["pressure_quantiles_m"]), c["pressure_quantiles_m"]
            )

    def test_zero_covariance_matches_stored_point_predictions(self):
        package = deepcopy(self.package)
        package["science"]["calibration"]["covariance"] = np.zeros((3, 3)).tolist()
        package["scientific_sha256"] = hashlib.sha256(
            canonical(package["science"]).encode()
        ).hexdigest()
        output = propagate(package, samples=2)
        failures = [
            r
            for r in package["science"]["engineering_agent"]["science"]["outputs"][
                "validate_selected"
            ]["records"]
            if not r["component_passes"]
        ]
        for prediction, record in zip(
            output["science"]["draws"][0]["records"], failures
        ):
            self.assertAlmostEqual(
                prediction["pressure_m"], record["component_pressure_m"], places=9
            )
            self.assertAlmostEqual(
                prediction["service_fraction"], record["component_service"], places=9
            )

    def test_invalid_covariance_and_budget_rejected(self):
        with self.assertRaises(ValueError):
            propagate(self.package, samples=1000)
        package = deepcopy(self.package)
        package["science"]["calibration"]["covariance"][0][0] = -1
        package["scientific_sha256"] = hashlib.sha256(
            canonical(package["science"]).encode()
        ).hexdigest()
        with self.assertRaises(ValueError):
            propagate(package, samples=2)


if __name__ == "__main__":
    unittest.main()
