import json, time, tempfile, unittest
from pathlib import Path
from fastapi.testclient import TestClient
from deva.api import create_app
from deva.digital_twin import experiment
from deva.twin_view import project
from deva.audit import verify_hash

RAW = json.loads(Path("examples/emergency_water_hydraulic.json").read_text())
D = [0.125] * 6


class TwinIntegrationTests(unittest.TestCase):
    def test_full_benchmark_exact_scientific_replay_and_projection(self):
        a = experiment(RAW, D)
        b = experiment(RAW, D)
        self.assertEqual(a["science"], b["science"])
        verify_hash(a)
        verify_hash(b)
        self.assertEqual(a["scientific_sha256"], b["scientific_sha256"])
        s = a["science"]
        self.assertNotIn("timestamp", s["engineering_agent"])
        self.assertTrue(s["cascade"]["events"])
        self.assertEqual(
            s["engineering_agent"]["science"]["outputs"]["calibrate_model"]["status"],
            "BENCHMARK CALIBRATED",
        )
        self.assertFalse(s["engineering_agent"]["science"]["target_achieved"])
        p = project(a)
        self.assertEqual(len(p["failed_cases"]), 4)
        self.assertEqual(p["unknown_cases"], [])
        for case in p["failed_cases"]:
            self.assertLess(case["component_pressure_m"], 15)
            self.assertFalse(case["state"]["result"]["passes"])
        self.assertEqual(len(p["frames"]), 9)
        self.assertFalse(p["counterexample"]["state"]["result"]["passes"])
        self.assertIsNone(
            p["counterexample"]["state"]["hydraulic"]["pressure_head_m"]["hospital"]
        )
        self.assertEqual(
            len(p["agent_candidates"]),
            len(
                s["engineering_agent"]["science"]["outputs"]["simulate_training"][
                    "candidates"
                ]
            ),
        )
        self.assertIn(
            "UNKNOWN", {state["category"] for state in s["digital_twin"]["states"]}
        )
        for f in p["cascade"]:
            for i, g in enumerate(f["gpu"]):
                self.assertEqual(
                    g["signed_velocity_ms"], f["state"]["hydraulic"]["velocity_ms"][i]
                )
                self.assertAlmostEqual(
                    g["flow_m3s"] * 3600, f["state"]["result"]["flow"][i]
                )
        ids = {r["observation"]["id"] for r in s["calibration"]["rows"]["calibration"]}
        self.assertFalse(
            ids
            & {r["observation"]["id"] for r in s["calibration"]["rows"]["validation"]}
        )

    def test_process_job_progress_contract_and_download(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            TestClient(create_app(directory)) as client,
        ):
            r = client.post(
                "/api/twin/jobs", json=dict(raw=RAW, diameters=D, seed=20261030)
            )
            self.assertEqual(r.status_code, 202, r.text)
            jid = r.json()["job_id"]
            deadline = time.monotonic() + 60
            while time.monotonic() < deadline:
                row = client.get("/api/jobs/" + jid).json()
                if row["status"] in ("completed", "failed"):
                    break
                time.sleep(0.1)
            self.assertEqual(row["status"], "completed", row)
            view = client.get("/api/jobs/" + jid + "/view")
            self.assertEqual(view.status_code, 200, view.text)
            self.assertEqual(
                view.json()["label"], "SYNTHETIC HIDDEN-PARAMETER BENCHMARK"
            )
            e = client.get("/api/jobs/" + jid + "/evidence").json()
            verify_hash(e)
            stream = client.get(
                "/api/jobs/" + jid + "/events", headers={"Accept-Encoding": "gzip"}
            )
            self.assertNotIn("content-encoding", stream.headers)
            events = stream.text
            for stage in (
                "observations",
                "calibration",
                "cascade",
                "engineering-agent",
                "completed",
            ):
                self.assertIn(stage, events)
            self.assertEqual(client.get("/api/twin/view").status_code, 200)
            self.assertEqual(client.get("/api/twin/nonsense").status_code, 404)

    def test_compression_preserves_values_and_streaming_headers(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            TestClient(create_app(directory)) as client,
        ):
            compressed = client.get(
                "/api/hydraulic/view", headers={"Accept-Encoding": "gzip"}
            )
            plain = client.get(
                "/api/hydraulic/view", headers={"Accept-Encoding": "identity"}
            )
            self.assertEqual(compressed.headers.get("content-encoding"), "gzip")
            self.assertNotIn("content-encoding", plain.headers)
            self.assertEqual(compressed.json(), plain.json())
            self.assertEqual(
                compressed.json()["experiment_id"], "deva-hydraulic-065f46bd63838ed5"
            )

    def test_strict_request_boundaries(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            TestClient(create_app(directory)) as client,
        ):
            for payload in [
                dict(raw=RAW, diameters=[0.1]),
                dict(raw=RAW, diameters=D, code="print(1)"),
                dict(raw=RAW, diameters=D, seed=-1),
                dict(raw=RAW, diameters=[-0.1] * 6),
            ]:
                self.assertEqual(
                    client.post("/api/twin/jobs", json=payload).status_code, 422
                )
            bad = json.loads(json.dumps(RAW))
            bad["minimum_pressure"]["unit"] = "m3/s"
            self.assertEqual(
                client.post(
                    "/api/twin/jobs", json=dict(raw=bad, diameters=D)
                ).status_code,
                422,
            )
