"""Replay the preserved cross-domain study at its clean recorded source revision."""

import gzip, json, os, subprocess, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
with gzip.open(ROOT / "artifacts/phase5-search-evidence.json.gz", "rt") as f:
    original = json.load(f)
revision = original["science"]["code"]["git_revision"]
if original["science"]["code"]["working_tree_dirty"]:
    raise ValueError("Pinned replay requires clean recorded sources")
with tempfile.TemporaryDirectory(prefix="deva-phase5-replay-") as directory:
    tree = Path(directory) / "source"
    output = Path(directory) / "replay.json"
    subprocess.run(
        ["git", "worktree", "add", "--detach", str(tree), revision],
        cwd=ROOT,
        check=True,
    )
    try:
        subprocess.run(
            [
                str(ROOT / ".venv/bin/python"),
                "-m",
                "deva.phase5_research",
                "--output",
                str(output),
            ],
            cwd=tree,
            env=dict(os.environ, PYTHONPATH=str(tree / "src")),
            check=True,
        )
        replay = json.loads(output.read_text())
        if (
            replay["science"] != original["science"]
            or replay["scientific_sha256"] != original["scientific_sha256"]
        ):
            raise ValueError(
                "Cross-domain scientific replay mismatch; original remains unchanged"
            )
        print(
            original["experiment_id"],
            "EXACT / 30 search trials, curves and decision analysis",
        )
    finally:
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(tree)], cwd=ROOT, check=True
        )
