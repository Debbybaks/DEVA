"""Presentation maintenance must preserve every immutable release artifact."""
import gzip
import hashlib
import json
import unittest
from pathlib import Path
from deva.audit import verify_hash

ROOT = Path(__file__).resolve().parents[1]

class EvidenceIntegrityTests(unittest.TestCase):
    def test_canonical_files_and_scientific_hashes_remain_exact(self):
        manifest = json.loads((ROOT / 'REPLAY_MANIFEST.json').read_text())
        self.assertEqual(len(manifest['checks']), 7)
        for check in manifest['checks']:
            with self.subTest(evidence=check['evidence_location']):
                path = ROOT / check['evidence_location']
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), check['sha256'])
                with (gzip.open(path, 'rt') if path.suffix == '.gz' else path.open()) as stream:
                    record = json.load(stream)
                for envelope in record if isinstance(record, list) else [record]:
                    verify_hash(envelope)
