import gzip, json, tempfile, unittest
from pathlib import Path
from fastapi.testclient import TestClient
from deva.api import create_app
from deva.audit import verify_hash

ROOT = Path(__file__).resolve().parents[1]


class WorldsTests(unittest.TestCase):
    def test_recovered_projection_and_progressive_api(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            TestClient(create_app(directory)) as client,
        ):
            manifest = client.get("/api/worlds/view")
            self.assertEqual(manifest.status_code, 200)
            record = manifest.json()
            verify_hash(record)
            rows = record["science"]["experiments"]
            self.assertEqual({e["domain"] for e in rows}, {"water", "microgrid"})
            self.assertEqual(len(rows), 30)
            self.assertTrue(all(not c["frames"] for e in rows for c in e["candidates"]))
            for domain in ["water", "microgrid"]:
                chosen = next(e for e in rows if e["domain"] == domain)
                response = client.get("/api/worlds/experiment/" + chosen["id"])
                self.assertEqual(response.status_code, 200)
                loaded = response.json()
                verify_hash(loaded)
                e = loaded["science"]["experiments"][0]
                self.assertTrue(any(c["frames"] for c in e["candidates"]))
                self.assertTrue(
                    all(
                        f["outcome"]["domain"] == domain
                        for c in e["candidates"]
                        for f in c["frames"]
                    )
                )
            self.assertEqual(
                client.get("/api/worlds/experiment/nonexistent").status_code, 404
            )

    def test_original_artifact_bytes_locked(self):
        import hashlib

        lock = json.loads((ROOT / "artifacts/phase5-baseline-lock.json").read_text())
        for name, value in lock["artifacts"].items():
            self.assertEqual(
                hashlib.sha256(
                    (ROOT / "artifacts" / f"{name}.json").read_bytes()
                ).hexdigest(),
                value["byte_sha256"],
            )
