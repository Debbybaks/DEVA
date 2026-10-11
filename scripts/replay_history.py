"""Replay immutable experiments in their recorded scientific source revision."""

import json, os, subprocess, tempfile, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# The Phase-3 scientific commit includes unchanged original/evolution engines.
REVISION = "118b7128d19805bcfe5b7c0da61cb76d90bd55ae"
checks = [
    (
        "emergency-water-evidence",
        "deva.cli",
        ["--seed", "20261011", "--samples", "200"],
        "emergency_water.json",
    ),
    (
        "evolution-evidence",
        "deva.evolve_cli",
        ["--seed", "20261013", "--generations", "3"],
        "emergency_water.json",
    ),
    (
        "hydraulic-evidence",
        "deva.hydraulic_experiment",
        ["--seed", "20261020"],
        "emergency_water_hydraulic.json",
    ),
]
with tempfile.TemporaryDirectory(prefix="deva-history-") as directory:
    tree = Path(directory) / "source"
    subprocess.run(
        ["git", "worktree", "add", "--detach", str(tree), REVISION],
        cwd=ROOT,
        check=True,
        stdout=subprocess.DEVNULL,
    )
    try:
        env = dict(os.environ, PYTHONPATH=str(tree / "src"))
        for artifact, module, args, problem in checks:
            output = Path(directory) / (artifact + ".json")
            subprocess.run(
                [
                    str(ROOT / ".venv/bin/python"),
                    "-m",
                    module,
                    str(tree / "examples" / problem),
                    *args,
                    "--output",
                    str(output),
                ],
                cwd=tree,
                env=env,
                check=True,
            )
            original = json.loads((ROOT / "artifacts" / f"{artifact}.json").read_text())
            replay = json.loads(output.read_text())
            assert (
                original["science"] == replay["science"]
            ), f"{artifact}: scientific mismatch"
            assert original["scientific_sha256"] == replay["scientific_sha256"]
            print(artifact, original["experiment_id"], "EXACT")
    finally:
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(tree)], cwd=ROOT, check=True
        )
