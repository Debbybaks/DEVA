"""Replay the immutable synthetic twin in its recorded scientific revision."""

import json
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
original = json.loads((ROOT / "artifacts/digital-twin-evidence.json").read_text())
science = original["science"]
revision = science["code"]["git_revision"]
if science["code"]["working_tree_dirty"]:
    raise ValueError("Cannot recover uncommitted scientific sources by revision alone")
with tempfile.TemporaryDirectory(prefix="deva-twin-replay-") as directory:
    tree = Path(directory) / "source"
    subprocess.run(
        ["git", "worktree", "add", "--detach", str(tree), revision],
        cwd=ROOT,
        check=True,
    )
    try:
        output = Path(directory) / "replay.json"
        subprocess.run(
            [
                str(ROOT / ".venv/bin/python"),
                "-c",
                "import json,sys;from deva.digital_twin import experiment;"
                "s=json.load(open(sys.argv[1]))['science'];"
                "r=experiment(s['configuration'],s['diameters_m'],s['seed']);"
                "json.dump(r,open(sys.argv[2],'w'))",
                str(ROOT / "artifacts/digital-twin-evidence.json"),
                str(output),
            ],
            cwd=tree,
            env=dict(os.environ, PYTHONPATH=str(tree / "src")),
            check=True,
        )
        replay = json.loads(output.read_text())
        if (
            replay["science"] != science
            or replay["scientific_sha256"] != original["scientific_sha256"]
        ):
            raise ValueError(
                "Twin scientific replay mismatch; do not overwrite original evidence"
            )
        agent = replay["science"]["engineering_agent"]["science"]
        validation = agent["outputs"]["validate_selected"]
        print(
            original["experiment_id"],
            "EXACT",
            f"{validation['failures']}/{validation['samples']} failures",
            "target established:",
            agent["target_achieved"],
        )
    finally:
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(tree)], cwd=ROOT, check=True
        )
