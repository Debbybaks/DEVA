import json, time, tempfile, unittest
from pathlib import Path
from fastapi.testclient import TestClient
from deva.api import create_app
from deva.audit import verify_hash
from deva.hydraulic_experiment import experiment
from deva.hydraulic_view import project

ROOT = Path(__file__).resolve().parents[1]


class HydraulicAPITests(unittest.TestCase):
    def setUp(self):
        self.raw = json.loads(
            (ROOT / "examples/emergency_water_hydraulic.json").read_text()
        )

    def test_intervention_audit_units_and_download(self):
        with tempfile.TemporaryDirectory() as d, TestClient(create_app(d)) as client:
            payload = dict(
                raw=self.raw,
                diameters_m=[0.1] * 6,
                closed=["east-trunk"],
                demand_factor=1.3,
                source_head_delta_m=-5.0,
            )
            r = client.post("/api/hydraulic/lab", json=payload)
            self.assertEqual(r.status_code, 200, r.text)
            data = r.json()
            verify_hash(data)
            self.assertTrue(data["causal_trace"]["facts"])
            self.assertFalse(data["state"]["result"]["passes"])
            self.assertEqual(
                data["science"]["verification_object"]["status"], "NUMERICAL_VALIDATION"
            )
            self.assertEqual(
                client.get("/api/hydraulic/lab/" + data["experiment_id"]).json()[
                    "science"
                ],
                data["science"],
            )
            self.assertEqual(
                client.post(
                    "/api/hydraulic/lab", json={**payload, "diameters_m": [0.1]}
                ).status_code,
                422,
            )
            bad = json.loads(json.dumps(payload))
            bad["raw"]["minimum_pressure"] = {"value": 15, "unit": "Pa"}
            self.assertEqual(
                client.post("/api/hydraulic/lab", json=bad).status_code, 422
            )

    def test_worker_job_has_hydraulic_contract_and_real_progress(self):
        with tempfile.TemporaryDirectory() as d, TestClient(create_app(d)) as client:
            r = client.post(
                "/api/hydraulic/jobs",
                json=dict(
                    raw=self.raw,
                    seed=5,
                    generations=1,
                    train_count=3,
                    validation_count=3,
                    test_count=4,
                ),
            )
            self.assertEqual(r.status_code, 202, r.text)
            jid = r.json()["job_id"]
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                status = client.get("/api/jobs/" + jid).json()
                if status["status"] in ["completed", "failed"]:
                    break
                time.sleep(0.05)
            self.assertEqual(status["status"], "completed", status)
            evidence = client.get("/api/jobs/" + jid + "/evidence").json()
            verify_hash(evidence)
            self.assertEqual(evidence["science"]["schema_version"], "3.0")
            view = client.get("/api/jobs/" + jid + "/view").json()
            self.assertEqual(
                view["recommendation"], evidence["science"]["recommendation"]
            )
            self.assertTrue(view["frames"])
            self.assertEqual(view["verification_objects"][0]["result"], "unsat")
            events = client.get("/api/jobs/" + jid + "/events").text
            self.assertIn("hydraulic_candidate", events)
            self.assertIn("completed", events)

    def test_projection_retains_closed_temporal_states_and_unknowns(self):
        envelope = experiment(self.raw, 2, 1, 3, 3, 3)
        view = project(envelope)
        self.assertEqual(view["frames"][6]["state"]["scenario"]["availability"][1], 0)
        self.assertEqual(view["cascade"][1]["state"]["result"]["service_fraction"], 0)
        for c in view["candidates"]:
            for s in c["states"]["heldout"]:
                if s:
                    self.assertEqual(len(s["result"]["flow"]), 6)
