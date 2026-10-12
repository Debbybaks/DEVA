import json, time, tempfile, unittest
from pathlib import Path
from fastapi.testclient import TestClient
from deva.api import create_app
from deva.audit import verify_hash


class DomainJobTests(unittest.TestCase):
    def test_both_registered_domains_background_evidence_and_projection(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            TestClient(create_app(directory)) as client,
        ):
            for name, path, budget in [
                ("microgrid", "microgrid.json", 300),
                ("water", "emergency_water_hydraulic.json", 500),
            ]:
                raw = json.loads(Path("examples/" + path).read_text())
                r = client.post(
                    "/api/domain/jobs",
                    json=dict(
                        domain=name,
                        raw=raw,
                        maximum_cost=float(budget),
                        maximum_candidates=3,
                        maximum_generations=1,
                        maximum_simulations=100,
                        training_samples=2,
                        validation_samples=2,
                        heldout_samples=4,
                    ),
                )
                self.assertEqual(r.status_code, 202, r.text)
                jid = r.json()["job_id"]
                deadline = time.monotonic() + 60
                while time.monotonic() < deadline:
                    row = client.get("/api/jobs/" + jid).json()
                    if row["status"] in ["completed", "failed"]:
                        break
                    time.sleep(0.05)
                self.assertEqual(row["status"], "completed", row)
                e = client.get("/api/jobs/" + jid + "/evidence").json()
                verify_hash(e)
                self.assertEqual(e["science"]["domain"]["id"], name)
                v = client.get("/api/domain/jobs/" + jid + "/view")
                self.assertEqual(v.status_code, 200, v.text)
                verify_hash(v.json())
                self.assertEqual(
                    v.json()["science"]["source_sha256"], e["scientific_sha256"]
                )
                events = client.get("/api/jobs/" + jid + "/events").text
                self.assertIn("scientific_result", events)

    def test_unknown_plugin_and_budgets_rejected(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            TestClient(create_app(directory)) as c,
        ):
            raw = json.loads(Path("examples/microgrid.json").read_text())
            self.assertEqual(
                c.post(
                    "/api/domain/jobs", json=dict(domain="generated-code", raw=raw)
                ).status_code,
                422,
            )
            self.assertEqual(
                c.post(
                    "/api/domain/jobs",
                    json=dict(domain="microgrid", raw=raw, maximum_simulations=999999),
                ).status_code,
                422,
            )
