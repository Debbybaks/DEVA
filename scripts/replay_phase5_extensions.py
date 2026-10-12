"""Replay larger validation/search science at its recorded source; ignore timing."""

import gzip, json, os, subprocess, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    with gzip.open(path, "rt") as f:
        return json.load(f)


validation = read(ROOT / "artifacts/phase5-validation-study.json.gz")
scale = read(ROOT / "artifacts/phase5-scale-search.json.gz")
revision = validation["science"]["code"]["git_revision"]
with tempfile.TemporaryDirectory(prefix="deva-phase5-extra-") as directory:
    tree = Path(directory) / "source"
    subprocess.run(
        ["git", "worktree", "add", "--detach", str(tree), revision],
        cwd=ROOT,
        check=True,
    )
    try:
        env = dict(os.environ, PYTHONPATH=str(tree / "src"))
        for script, artifact, original in [
            (
                "phase5_validation_study.py",
                "phase5-validation-study.json.gz",
                validation,
            ),
            ("phase5_scale.py", "phase5-scale-search.json.gz", scale),
        ]:
            subprocess.run(
                [str(ROOT / ".venv/bin/python"), str(ROOT / "scripts" / script)],
                cwd=tree,
                env=env,
                check=True,
            )
            replay = read(tree / "artifacts" / artifact)
            if isinstance(original, list) and len(original) != len(replay):
                raise ValueError("Replay result count mismatch")
            pairs = (
                zip(original, replay)
                if isinstance(original, list)
                else [(original, replay)]
            )
            for first, second in pairs:
                if (
                    first["science"] != second["science"]
                    or first["scientific_sha256"] != second["scientific_sha256"]
                ):
                    raise ValueError(f"{artifact}: scientific mismatch")
            print(artifact, "EXACT")
    finally:
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(tree)], cwd=ROOT, check=True
        )
