import json
from pathlib import Path
import unittest
import tempfile
from deva.general_engineer import investigate, ExperimentMemory, dominates
from deva.domains.water import WaterDomain
from deva.domains.microgrid import MicrogridDomain
from deva.audit import verify_hash

ROOT = Path(__file__).resolve().parents[1]


class GeneralEngineerTests(unittest.TestCase):
    def test_same_engine_both_domains(self):
        for domain in [
            WaterDomain(
                json.loads(
                    (ROOT / "examples/emergency_water_hydraulic.json").read_text()
                )
            ),
            MicrogridDomain(json.loads((ROOT / "examples/microgrid.json").read_text())),
        ]:
            e = investigate(
                domain,
                maximum_candidates=4,
                maximum_generations=1,
                maximum_simulations=80,
                training_samples=2,
                validation_samples=2,
                heldout_samples=4,
            )
            verify_hash(e)
            s = e["science"]
            self.assertEqual(s["domain"]["id"], domain.descriptor["id"])
            self.assertIsNotNone(s["heldout"])
            self.assertFalse(s["target_achieved"])
            self.assertTrue(
                all(
                    x["output"]["domain"] == domain.descriptor["id"]
                    for x in s["invocations"]
                )
            )

    def test_simulation_budget_preserves_partial_evidence(self):
        d = MicrogridDomain(json.loads((ROOT / "examples/microgrid.json").read_text()))
        s = investigate(
            d,
            maximum_simulations=1,
            training_samples=2,
            validation_samples=2,
            heldout_samples=2,
        )["science"]
        self.assertEqual(s["solver_calls"], 1)
        self.assertIsNone(s["heldout"])
        self.assertTrue(s["invocations"])
        self.assertIn("INCOMPLETE", s["candidates"][0]["rejection_reason"])

    def test_memory_is_domain_and_configuration_scoped(self):
        d = MicrogridDomain(json.loads((ROOT / "examples/microgrid.json").read_text()))
        m = ExperimentMemory()
        args = dict(
            maximum_generations=0,
            training_samples=2,
            validation_samples=2,
            heldout_samples=2,
            memory=m,
        )
        first = investigate(d, **args)
        second = investigate(d, **args)
        self.assertEqual(first["science"]["solver_calls"], 14)
        self.assertEqual(second["science"]["solver_calls"], 0)
        self.assertEqual(first["science"]["heldout"], second["science"]["heldout"])

    def test_frontier_dominance_is_not_scalar_score(self):
        a = dict(cost=10, training=dict(failures=1, mean_service=0.8))
        b = dict(cost=12, training=dict(failures=1, mean_service=0.7))
        self.assertTrue(dominates(a, b))
        self.assertFalse(dominates(b, a))

    def test_durable_memory_checksum(self):
        d = MicrogridDomain(json.loads((ROOT / "examples/microgrid.json").read_text()))
        m = ExperimentMemory()
        investigate(
            d,
            maximum_generations=0,
            training_samples=2,
            validation_samples=2,
            heldout_samples=2,
            memory=m,
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "memory.json"
            m.save(path)
            restored = ExperimentMemory.load(path)
            self.assertEqual(m.records, restored.records)
            value = json.loads(path.read_text())
            next(iter(value["records"].values()))["sha256"] = "0" * 64
            path.write_text(json.dumps(value))
            with self.assertRaises(ValueError):
                ExperimentMemory.load(path)
