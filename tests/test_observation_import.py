import unittest
from copy import deepcopy
from deva.observation_import import import_batch


class ImportTests(unittest.TestCase):
    def batch(self):
        return dict(
            domain="microgrid",
            provenance=dict(kind="SYNTHETIC", source="reproducible import fixture"),
            records=[
                dict(
                    id="o1",
                    timestamp="2026-10-12T00:00:00Z",
                    component="solar",
                    sensor="s1",
                    quantity="power",
                    measurement=dict(value=2, unit="kW"),
                    uncertainty=dict(value=100, unit="W"),
                    split="calibration",
                )
            ],
        )

    def test_units_provenance_and_missing_retained(self):
        p = self.batch()
        p["records"].append(
            dict(p["records"][0], id="o2", measurement=None, split="validation")
        )
        r = import_batch(p, "microgrid", {"power": "W"}, {"solar"})
        self.assertEqual(r["accepted"][0]["canonical_value"], 2000)
        self.assertEqual(r["quality"], dict(total=2, accepted=1, missing=1))
        self.assertEqual(r["status"], "INGESTED / NOT CALIBRATED")

    def test_domain_units_and_timezone_rejected(self):
        p = self.batch()
        with self.assertRaises(ValueError):
            import_batch(p, "water", {"power": "W"}, {"solar"})
        p["records"][0]["measurement"]["unit"] = "J"
        with self.assertRaises(ValueError):
            import_batch(p, "microgrid", {"power": "W"}, {"solar"})

    def test_explicit_split_and_sensor_identity(self):
        p = self.batch()
        p["records"][0]["split"] = "training"
        with self.assertRaises(ValueError):
            import_batch(p, "microgrid", {"power": "W"}, {"solar"})
