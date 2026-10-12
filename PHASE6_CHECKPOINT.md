# Phase 6 — release candidate checkpoint

Recovered clean Phase-5 HEAD: 15c812141e3c90da96ea77ddbb8408ece7c1e41f. Scope is frozen; no new domain or scientific research subsystem was introduced.

Completed: release scope/gates; same-origin production entry point; public scientific-write denial and labelled archive UX; public/local runtime isolation; container configuration; complete Python dependency/build pins; clean-room installation/build; security/privacy/dependency and bounded-claim audit; release notes/report/README; canonical replay manifest; test/replay evidence; native production smoke/screenshots; reproducibility archive tooling.

Validation: full 121 Python tests PASS plus final two affected release-boundary tests; 15 frontend; eight isolated browser tests; strict production build; seven exact replay checks; all immutable evidence bytes retained. Original five-second startup assertion unchanged. Clean environment: seven domain-contract/analytical plus two production tests pass, npm ci/build pass. Production dependency audit: zero known npm production vulnerabilities.

Preserved failed attempts: concurrent solvers caused startup timeouts; a clean frontend build competing with background evolution yielded ~63.5 s job latency beyond the unchanged 60 s test. Isolated full browser suite passes. No valid assertion was weakened. Public runtime isolation is independently protected; no unobserved database failure is invented as the cause of the timed-out run.

Scientific findings unchanged: 38/200; 44→13/200 at higher cost; 4/40 and 2% UNESTABLISHED; fresh 22→7→5/120, +8.47 known intermediate relaxation not global minimum; 93/512 water and 300/512 microgrid; larger 16/120 and 31/120 searches; no general guided-search superiority.

BLOCKED: actual public deployment and public smoke. No DEVA hosting project or Git remote exists; the connected Vercel account only has unrelated projects. Runtime has no suitable hosting credentials. Do not replace unrelated projects or create a new account/project ownership decision speculatively. Docker daemon execution is sandbox-blocked; native production serving is qualified but image execution is not claimed.

No final v1.0.0 tag or PROJECT_COMPLETE.md has been created. Do not call v1.0 complete until gates L/M pass. All research limitations remain in V1_SCOPE.md and FUTURE_RESEARCH.md.

## Resume

1. Identify the RC commit/tag with `git rev-parse v1.0.0-rc.1^{commit}` and check clean tree.
2. Supply an authorised persistent-container hosting target/credentials, or validate an explicitly chosen equivalent hosting configuration without rewriting the scientific system.
3. Build/deploy Dockerfile, health `/api/health`, port 8000, read-only `deva.release_app:app` (never public `deva.api:app`). Record stable public URL/deployment ID.
4. From apps/command run `node scripts/release-smoke.mjs https://CANONICAL_URL ../../artifacts/release/public` and inspect actual public evidence/domain/health responses against REPLAY_MANIFEST.json.
5. After initial public gates pass, prepare final version/metadata and PROJECT_COMPLETE.md; commit, deploy and smoke-test that exact final commit, then create immutable v1.0.0. Resolve the release commit through the tag rather than embedding a self-referential hash. Never move a release tag.
6. Rebuild archive with `scripts/package_release.py --tag v1.0.0`; leave clean; stop feature development.

Local commands: README.md. Full validation need not repeat absent relevant changes; deployment smoke must actually use the public URL. Release state and scientific source identities are separately recorded to avoid embedding an impossible self-referential commit hash in a committed manifest.
