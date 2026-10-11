import json
from pathlib import Path
import tempfile
import time
import unittest
from fastapi.testclient import TestClient
from deva.api import create_app
from deva.jobs import JobStore

ROOT = Path(__file__).resolve().parents[1]


class APITests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.client_context = TestClient(create_app(self.directory.name))
        self.client = self.client_context.__enter__()
        self.raw = json.loads((ROOT / "examples/emergency_water.json").read_text())

    def tearDown(self):
        self.client_context.__exit__(None, None, None)
        self.directory.cleanup()

    def test_health_baseline_and_contract(self):
        self.assertEqual(self.client.get("/api/health").status_code, 200)
        science = self.client.get("/api/evidence/baseline").json()["science"]
        self.assertEqual(science["candidates"][2]["uncertainty"]["failures"], 38)
        self.assertEqual(self.client.get("/api/evidence/unknown").status_code, 404)
        self.assertEqual(self.client.get("/api/jobs/../../etc/passwd").status_code, 404)
        self.assertEqual(
            self.client.post(
                "/api/jobs", json=dict(raw=self.raw, generations=99)
            ).status_code,
            422,
        )
        self.assertEqual(
            self.client.post(
                "/api/jobs", json=dict(raw=self.raw, seed=True)
            ).status_code,
            422,
        )
        self.assertEqual(
            self.client.post("/api/jobs", json=dict(raw=self.raw, extra=1)).status_code,
            422,
        )

    def test_interactive_outage_source_loss_and_invalid_arrays(self):
        request = dict(
            raw=self.raw,
            capacities=[66.5, 66.5, 38.0, 28.5, 38.0, 28.5],
            availability=[1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
        )
        result = self.client.post("/api/lab", json=request)
        self.assertEqual(result.status_code, 200, result.text)
        self.assertTrue(result.json()["result"]["passes"])
        request["source_losses"] = ["source-west", "source-east"]
        result = self.client.post("/api/lab", json=request)
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(result.json()["result"]["service_fraction"], 0)
        request["availability"] = [1.0]
        self.assertEqual(self.client.post("/api/lab", json=request).status_code, 422)

    def test_background_job_progress_cache_and_evidence(self):
        request = dict(
            raw=self.raw,
            seed=123,
            generations=1,
            train_samples=3,
            validation_samples=3,
            test_samples=3,
        )
        response = self.client.post("/api/jobs", json=request)
        self.assertEqual(response.status_code, 202, response.text)
        jid = response.json()["job_id"]
        # Main API stays responsive while a different process computes.
        self.assertEqual(self.client.get("/api/health").status_code, 200)
        again = self.client.post("/api/jobs", json=request)
        self.assertTrue(again.json()["cached"])
        self.assertEqual(again.json()["job_id"], jid)
        deadline = time.monotonic() + 40
        while time.monotonic() < deadline:
            state = self.client.get("/api/jobs/" + jid).json()
            if state["status"] in ("completed", "failed", "cancelled"):
                break
            time.sleep(0.05)
        self.assertEqual(state["status"], "completed", state)
        evidence = self.client.get("/api/jobs/" + jid + "/evidence").json()
        self.assertEqual(evidence["science"]["experiment_config"]["seed"], 123)
        events = self.client.get("/api/jobs/" + jid + "/events").text
        self.assertIn("selection_frozen", events)
        self.assertIn("completed", events)
        self.assertEqual(self.client.delete("/api/jobs/" + jid).status_code, 409)

    def test_unknown_job(self):
        self.assertEqual(self.client.get("/api/jobs/" + "0" * 32).status_code, 404)
