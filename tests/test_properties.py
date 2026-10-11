"""Seeded generated-graph invariants and new evidence/API regressions."""

import copy
import json
from pathlib import Path
import tempfile
import time
import unittest
import numpy as np
from fastapi.testclient import TestClient
from deva.schema import Problem
from deva.model import Scenario, simulate
from deva.audit import audit_result, verify_hash
from deva.adversary import topology_cuts
from deva.evolution import evolve
from deva.report import render
from deva.api import create_app
from test_core import chain

ROOT = Path(__file__).resolve().parents[1]


class GeneratedGraphTests(unittest.TestCase):
    def test_seeded_dag_conservation_monotonicity_and_independent_audit(self):
        rng = np.random.default_rng(143)
        for trial in range(15):
            nodes = [f"n{i}" for i in range(5)]
            edges = [
                dict(
                    id=f"e{i}-{j}",
                    tail=nodes[i],
                    head=nodes[j],
                    unit_cost=1,
                    max_capacity=30,
                    corridor=str(i % 2),
                )
                for i in range(4)
                for j in range(i + 1, 5)
                if j == i + 1 or rng.random() < 0.5
            ]
            raw = dict(
                id=f"dag-{trial}",
                objective="Generated conservation test",
                nodes=nodes,
                edges=edges,
                supply={nodes[0]: 50},
                demand={nodes[3]: 8, nodes[4]: 12},
                budget=1000,
                target=0.95,
            )
            p = Problem.parse(raw)
            c = rng.uniform(0, 20, len(edges)).tolist()
            scenario = Scenario(
                "generated", tuple(rng.uniform(0.2, 1, len(edges))), 0.9, 1.1
            )
            a = simulate(p, c, scenario)
            audit_result(p, c, scenario, a)
            b = simulate(p, [v + 5 for v in c], scenario)
            self.assertGreaterEqual(b["service_fraction"] + 1e-7, a["service_fraction"])
            self.assertGreaterEqual(sum(b["delivered"]) + 1e-6, sum(a["delivered"]))

    def test_co_located_source_demand_has_no_pipe_only_cut(self):
        raw = chain()
        raw["demand"] = {"s": 10}
        p = Problem.parse(raw)
        result = topology_cuts(p, [10, 10])[0]
        self.assertIsNone(result["minimum_pipe_outages"])

    def test_all_infeasible_synthesis_attempts_preserved(self):
        raw = chain()
        raw["budget"] = 1
        s = evolve(raw, 1, 1, 2, 2, 2)["science"]
        self.assertIsNone(s["recommendation"])
        operators = {a["operator"] for a in s["infeasible_attempts"]}
        self.assertEqual(
            operators, {"nominal_lp", "declared_scenario_lp", "outage_demand_cross_lp"}
        )
        self.assertTrue(
            all(
                a["id"] and a["status"] == "infeasible"
                for a in s["infeasible_attempts"]
            )
        )

    def test_report_contains_negative_results_and_never_claims_proof(self):
        envelope = json.loads((ROOT / "artifacts/evolution-evidence.json").read_text())
        text = render(envelope)
        self.assertIn("g0-c000", text)
        self.assertIn("held-out", text.lower())
        self.assertIn(
            "No numerical simulation or Monte Carlo result is mathematical or formal verification",
            text,
        )
        verify_hash(envelope)


class DurableAPIRegressionTests(unittest.TestCase):
    def test_interactive_evidence_is_reproducible_and_downloadable(self):
        raw = json.loads((ROOT / "examples/emergency_water.json").read_text())
        req = dict(
            raw=raw,
            capacities=[66.5, 66.5, 38.0, 28.5, 38.0, 28.5],
            availability=[0.0, 1.0, 1.0, 1.0, 1.0, 1.0],
            demand_factor=1.35,
        )
        with (
            tempfile.TemporaryDirectory() as directory,
            TestClient(create_app(directory)) as c,
        ):
            first = c.post("/api/lab", json=req).json()
            second = c.post("/api/lab", json=req).json()
            self.assertEqual(first["experiment_id"], second["experiment_id"])
            self.assertEqual(first["science"], second["science"])
            verify_hash(first)
            saved = c.get("/api/lab/" + first["experiment_id"])
            self.assertEqual(saved.status_code, 200)
            verify_hash(saved.json())
            self.assertFalse(saved.json()["result"]["passes"])
            self.assertEqual(c.get("/api/lab/bad").status_code, 404)

    def test_cancellation_terminal_state_retained(self):
        raw = json.loads((ROOT / "examples/emergency_water.json").read_text())
        with (
            tempfile.TemporaryDirectory() as directory,
            TestClient(create_app(directory)) as c,
        ):
            reply = c.post(
                "/api/jobs",
                json=dict(
                    raw=raw,
                    seed=453,
                    generations=3,
                    train_samples=60,
                    validation_samples=80,
                    test_samples=200,
                ),
            )
            jid = reply.json()["job_id"]
            self.assertEqual(c.delete("/api/jobs/" + jid).status_code, 202)
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                status = c.get("/api/jobs/" + jid).json()
                if status["status"] in ("cancelled", "failed", "completed"):
                    break
                time.sleep(0.03)
            self.assertEqual(status["status"], "cancelled")
            events = c.get("/api/jobs/" + jid + "/events").text
            self.assertIn("cancelled", events)
            self.assertEqual(c.get("/api/jobs/" + jid + "/evidence").status_code, 409)
