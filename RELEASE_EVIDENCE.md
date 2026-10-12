# DEVA v1.0 release evidence

Local and actual public release qualification pass. Public evidence: artifacts/release/public-final/. The final tag points to the exact requalified production metadata commit.

Machine-readable validation: artifacts/release/validation.json. Canonical replay manifest: REPLAY_MANIFEST.json. Raw test/build/replay logs, dependency audit, local production smoke and representative screenshots: artifacts/release/. Current scientific report: DEVA_V1_TECHNICAL_REPORT.md incorporating the unchanged Phase-5 report.

121 Python tests pass; the final runtime-isolation edit also passes both targeted release-boundary tests. 15 frontend tests, eight isolated browser tests and production build pass. Seven pinned checks reproduce exactly; artifact byte hashes remain unchanged. Both domains' investigations, ablation, budget negotiation and bounded proofs are covered by these immutable collections.

Two contended browser attempts are retained. Initial concurrent science/browser work produced three five-second startup failures; concurrent clean frontend build caused a background job to finish around 63.5 seconds, exceeding the unchanged 60-second job assertion. Without those competing loads all eight pass. No test or timeout was weakened.

Clean-room Python 3.12 environment: full dependency closure installed; editable package installed; seven domain-contract/analytical tests and two production tests pass. Clean frontend npm ci and build pass using a writable temporary npm cache. Managed-environment npm audit reports zero known production vulnerabilities. This does not prove absence of vulnerabilities. Container execution is unvalidated because Docker daemon access is sandbox-blocked.

Local native production smoke includes same-origin assets/API, both worlds, evidence/uncertainty/X-ray, researcher/judge/portfolio, stored demonstration, 390 px width, keyboard focus, reduced motion, public scientific-write denial and 404 recovery. It is explicitly not a public deployment test. Performance timings are environment-specific.

The public archive is read-only. New autonomous investigations remain available in the trusted local scientific environment; public multi-tenant live compute is outside frozen v1.0. No field data, calibrated rupture prediction, AC dynamics or universal reliability claim is implied. The 2% target remains unestablished.

Release archive command after RC tagging: `.venv/bin/python scripts/package_release.py`. It includes Git history needed for pinned old-source replays, tagged source and built frontend with checksums. Public URL and final tag must only be populated after authorised deployment and public smoke gates pass.

Actual public native-container smoke PASS, version 1.0.0. Public startup samples include 2.23 s and 6.75 s across independent runs; cold/network variation remains visible. The local unchanged five-second startup assertion continues to pass. No universal public startup bound is claimed.
