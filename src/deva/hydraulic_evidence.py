"""Property-specific numerical evidence; no inference of whole-system proof."""

import math
import hashlib
import json
import platform
import subprocess
from pathlib import Path
import numpy as np
import scipy
from .experiment import canonical
from .hydraulic_v2 import parse, VERSION, G, MASS_TOL, ENERGY_TOL, cost


def audit(raw, diameters, scenario, result):
    m = parse(raw)
    names = [n["id"] for n in m["nodes"]]
    pipes = m["pipes"]
    q = result["flow_m3s"]
    heads = result["head_m"]
    requested = result["requested_m3s"]
    delivery = result["delivered_m3s"]
    closed = set(scenario.get("closed", []))
    lost = set(scenario.get("source_losses", []))
    if (
        len(q) != len(pipes)
        or set(heads) != set(names)
        or any(not math.isfinite(v) for v in q)
    ):
        raise ValueError("Malformed state")
    reachable = set(m["sources"]) - lost
    while True:
        grown = (
            reachable
            | {
                e["head"]
                for e in pipes
                if e["id"] not in closed and e["tail"] in reachable
            }
            | {
                e["tail"]
                for e in pipes
                if e["id"] not in closed and e["head"] in reachable
            }
        )
        if grown == reachable:
            break
        reachable = grown
    if any((heads[n] is None) != (n not in reachable) for n in names):
        raise ValueError("Forged connectivity/unknown head")
    mass = energy = 0.0
    for n in m["nodes"]:
        name = n["id"]
        d = n["demand"] * scenario.get("demand_factor", 1.0)
        if abs(requested[name] - d) > MASS_TOL:
            raise ValueError("Requested demand mismatch")
        h = heads[name]
        expected = (
            d * math.sqrt(min(max((h - n["z"]) / m["pfull"], 0), 1))
            if h is not None
            else 0.0
        )
        if abs(delivery[name] - expected) > MASS_TOL:
            raise ValueError("Pressure-dependent service mismatch")
        pressure = (h - n["z"]) if h is not None else None
        if pressure != result["pressure_head_m"][name]:
            raise ValueError("Pressure mismatch")
        net = sum(q[j] for j, e in enumerate(pipes) if e["head"] == name) - sum(
            q[j] for j, e in enumerate(pipes) if e["tail"] == name
        )
        if name not in m["sources"] or name in lost:
            mass = max(mass, abs(net - delivery[name]))
        else:
            expected_head = scenario.get("head_overrides_m", {}).get(
                name,
                m["sources"][name]["head"] + scenario.get("source_head_delta_m", 0.0),
            )
            if (
                abs(h - expected_head) > ENERGY_TOL
                or abs(result["boundary_injection_m3s"][name] + net) > MASS_TOL
            ):
                raise ValueError("Boundary mismatch")
    for j, e in enumerate(pipes):
        if (
            abs(result["velocity_ms"][j] - 4 * q[j] / (math.pi * diameters[j] ** 2))
            > 1e-7
        ):
            raise ValueError("Velocity mismatch")
        if e["id"] in closed or heads[e["tail"]] is None:
            if abs(q[j]) > MASS_TOL:
                raise ValueError("Closed/unanchored pipe carries flow")
            continue
        r = (
            8
            * e["friction"]
            * scenario.get("friction_factor", 1.0)
            * e["length"]
            / (G * math.pi**2 * diameters[j] ** 5)
        )
        energy = max(
            energy, abs(heads[e["tail"]] - heads[e["head"]] - r * q[j] * abs(q[j]))
        )
        if (
            abs(result["velocity_ms"][j] - 4 * q[j] / (math.pi * diameters[j] ** 2))
            > 1e-7
        ):
            raise ValueError("Velocity mismatch")
    if mass > MASS_TOL or energy > ENERGY_TOL:
        raise ValueError("Independent hydraulic residual failure")
    demand_nodes = [n["id"] for n in m["nodes"] if n["demand"] > 0]
    sf = min(delivery[n] / requested[n] for n in demand_nodes)
    req = {
        "service": sf >= m["target"] - 1e-7,
        "pressure": all(
            heads[n] is not None
            and heads[n] - next(x["z"] for x in m["nodes"] if x["id"] == n)
            >= m["pmin"] - ENERGY_TOL
            for n in demand_nodes
        ),
        "velocity": all(
            abs(4 * f / (math.pi * d * d)) <= m["vmax"] + 1e-7
            for f, d in zip(q, diameters)
        ),
        "source_supply": all(
            -MASS_TOL <= v <= m["sources"][n]["maximum_supply"] + MASS_TOL
            for n, v in result["boundary_injection_m3s"].items()
        ),
        "budget": cost(m, diameters) <= m["budget"] + 1e-7,
    }
    if (
        req != result["requirements"]
        or all(req.values()) != result["passes"]
        or abs(sf - result["service_fraction"]) > 1e-7
    ):
        raise ValueError("Forged requirement result")
    return dict(
        property="Continuity, Darcy energy, PDD delivery, boundaries and feasibility recomputed from outputs",
        result="pass",
        status="NUMERICAL_VALIDATION",
        mass_residual_m3s=mass,
        energy_residual_m=energy,
        tolerances={"mass_m3s": MASS_TOL, "energy_m": ENERGY_TOL},
        limitations=[
            "Floating point numerical audit, not exact proof or field calibration"
        ],
    )


def topology_verification(raw, max_outages=1):
    """SMT checks all bounded pipe-outage assignments, not sampled scenarios."""
    import z3

    m = parse(raw)
    names = [n["id"] for n in m["nodes"]]
    if (
        isinstance(max_outages, bool)
        or not isinstance(max_outages, int)
        or not 0 <= max_outages <= len(m["pipes"])
    ):
        raise ValueError("Invalid outage bound")
    context = z3.Context(proof=True)
    solver = z3.Solver(ctx=context)
    solver.set(timeout=10000)
    available = [z3.Bool(f"open_{j}", ctx=context) for j in range(len(m["pipes"]))]
    solver.add(z3.PbLe([(z3.Not(a), 1) for a in available], max_outages))
    reach = {n: z3.BoolVal(n in m["sources"], ctx=context) for n in names}
    for _ in range(len(names) - 1):
        reach = {
            n: z3.Or(
                reach[n],
                *[
                    z3.And(
                        available[j], reach[e["head"] if e["tail"] == n else e["tail"]]
                    )
                    for j, e in enumerate(m["pipes"])
                    if n in (e["tail"], e["head"])
                ],
            )
            for n in names
        }
    targets = [n["id"] for n in m["nodes"] if n["demand"] > 0]
    solver.add(z3.Not(z3.And(*[reach[n] for n in targets])))
    smt = solver.to_smt2()
    answer = solver.check()
    proof = solver.proof().sexpr() if answer == z3.unsat else None
    witness = (
        [
            e["id"]
            for e, a in zip(m["pipes"], available)
            if z3.is_false(solver.model().eval(a, model_completion=True))
        ]
        if answer == z3.sat
        else None
    )
    return dict(
        requirement_id="R-TOPOLOGY-BOUNDED",
        property=f"Every demand node connects to an active source after at most {max_outages} pipe outages",
        assumptions=[
            "Undirected passive hydraulic topology",
            "All source boundaries active",
            "No demand/pressure/flow guarantee",
            "Finite explicit graph and pipe-only failures",
        ],
        model_version=VERSION,
        tool="Z3 " + z3.get_version_string(),
        inputs={
            "node_ids": names,
            "pipe_ids": [e["id"] for e in m["pipes"]],
            "maximum_outages": max_outages,
            "pipe_topology": [
                {"id": e["id"], "tail": e["tail"], "head": e["head"]}
                for e in m["pipes"]
            ],
            "active_sources": list(m["sources"]),
            "demand_nodes": targets,
        },
        result=str(answer),
        status=(
            "FORMALLY VERIFIED"
            if answer == z3.unsat
            else ("COUNTEREXAMPLE" if answer == z3.sat else "UNKNOWN")
        ),
        smtlib=smt,
        proof=proof,
        proof_sha256=hashlib.sha256(proof.encode()).hexdigest() if proof else None,
        counterexample_closed=witness,
        scope="Only bounded Boolean connectivity; no promotion of hydraulic service or entire design",
        limitations=[
            "Proof generated by Z3, not independently proof-kernel checked",
            "Reachability encoding validated against exhaustive enumeration in tests",
        ],
    )


def provenance_revision():
    root = Path(__file__).resolve().parents[2]
    revision = subprocess.run(
        ["git", "log", "-1", "--format=%H", "--", "src/deva"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    dirty = bool(
        subprocess.run(
            ["git", "status", "--porcelain", "--", "src/deva"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    )
    source_hash = hashlib.sha256(
        b"".join(p.read_bytes() for p in sorted((root / "src/deva").glob("*.py")))
    ).hexdigest()
    return {
        "git_revision": revision,
        "working_tree_dirty": dirty,
        "scientific_source_sha256": source_hash,
    }


def envelope(science):
    from datetime import datetime, timezone

    digest = hashlib.sha256(canonical(science).encode()).hexdigest()
    return dict(
        experiment_id="deva-hydraulic-" + digest[:16],
        scientific_sha256=digest,
        timestamp=datetime.now(timezone.utc).isoformat(),
        science=science,
    )
