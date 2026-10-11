"""Domain-independent recursive scientific source identity; legacy hashes stay intact."""

import hashlib
from pathlib import Path
import subprocess


def source_revision():
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
    files = sorted((root / "src/deva").rglob("*.py"))
    digest = hashlib.sha256()
    for p in files:
        name = str(p.relative_to(root)).encode()
        body = p.read_bytes()
        digest.update(
            len(name).to_bytes(8, "big") + name + len(body).to_bytes(8, "big") + body
        )
    return dict(
        git_revision=revision,
        working_tree_dirty=dirty,
        scientific_source_sha256=digest.hexdigest(),
        hash_scope="Length-prefixed paths and contents of every Python module recursively",
    )
