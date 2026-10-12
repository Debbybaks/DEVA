import unittest
from deva.hypotheses import update


class HypothesisTests(unittest.TestCase):
    def test_evidence_required_and_domain_local(self):
        h = dict(
            id="H1",
            domain="water",
            status="PROPOSED",
            statement="A capacity intervention improves this witnessed scenario",
        )
        h = update(h, "TESTING", [])
        with self.assertRaises(ValueError):
            update(h, "SUPPORTED", [])
        with self.assertRaises(ValueError):
            update(
                h, "SUPPORTED", [dict(domain="microgrid", reference="e1", scope="toy")]
            )
        final = update(
            h,
            "SUPPORTED",
            [
                dict(
                    domain="water",
                    reference="e1/inputs",
                    scope="one model intervention, not field causality",
                )
            ],
        )
        self.assertEqual(final["status"], "SUPPORTED")
        self.assertEqual(h["status"], "TESTING")

    def test_invalid_lifecycle_rejected(self):
        with self.assertRaises(ValueError):
            update(dict(domain="water", status="PROPOSED"), "REJECTED", [])
