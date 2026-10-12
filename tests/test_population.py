import json, unittest
from pathlib import Path
from deva.domains.microgrid import MicrogridDomain
from deva.population import evaluate_population


class PopulationTests(unittest.TestCase):
    def test_sampling_scopes_and_replay(self):
        d = MicrogridDomain(json.loads(Path("examples/microgrid.json").read_text()))
        a = evaluate_population(d, d.baseline, 42, 8)
        self.assertEqual(
            a["science"], evaluate_population(d, d.baseline, 42, 8)["science"]
        )
        self.assertIsNotNone(a["science"]["wilson_95"])
        self.assertIsNone(
            evaluate_population(d, d.baseline, 42, 8, "adversarial")["science"][
                "wilson_95"
            ]
        )

    def test_population_admission(self):
        d = MicrogridDomain(json.loads(Path("examples/microgrid.json").read_text()))
        with self.assertRaises(ValueError):
            evaluate_population(d, d.baseline, 42, 1000000)
