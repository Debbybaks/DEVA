import unittest
from fastapi.testclient import TestClient
from deva.release_app import app

class ReleaseTests(unittest.TestCase):
    def test_visual_root_and_explicit_archive(self):
        with TestClient(app) as c:
            for route in ["/", "/?utm_source=chatgpt.com", "/archive", "/archive/"]:
                response = c.get(route, follow_redirects=False)
                self.assertEqual(response.status_code, 200)
                self.assertIn('id="root"', response.text)
                self.assertEqual(response.headers["content-type"], "text/html; charset=utf-8")
                self.assertEqual(c.post(route, json={}).status_code, 403)
    def test_public_mutations_denied(self):
        with TestClient(app) as c:
            for route in ["/api/domain/jobs", "/api/jobs", "/api/hydraulic/lab", "/api/twin/jobs"]:
                self.assertEqual(c.post(route, json={}).status_code, 403)
            self.assertEqual(c.delete("/api/jobs/test").status_code, 403)
            self.assertEqual(app.state.jobs.directory.name, "public-archive")
            response = c.get("/api/health")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers["x-content-type-options"], "nosniff")
    def test_unknown_api_and_asset_paths(self):
        with TestClient(app) as c:
            self.assertEqual(c.get("/api/not-a-route").status_code, 404)
            self.assertEqual(c.get("/missing-secret.env").status_code, 404)
            self.assertEqual(c.get("/%2e%2e/pyproject.toml").status_code, 404)
