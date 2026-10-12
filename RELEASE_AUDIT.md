# v1.0 release audit

Baseline: 15c812141e3c90da96ea77ddbb8408ece7c1e41f, clean. Scientific source was not rewritten. Existing core/domain isolation, numerical audits and analytical cases remain protected by the full suite and pinned historical replays.

## Findings and disposition

* No deployment configuration existed. Added a same-origin container-serving entry point; read-only public mode blocks all scientific mutations. Existing trusted local workers and investigation controls remain intact.
* Existing generated job paths validate hexadecimal UUIDs; evidence routes use fixed names or validated hexadecimal content IDs. Production static paths resolve beneath the dist root. Unknown API/static paths return 404.
* Scientific tools are registered functions. No eval/generated code, shell=True or unrestricted user command execution exists. Git subprocesses have fixed argument lists for provenance.
* Local API is intentionally not multi-tenant/authenticated. Public deployment uses deva.release_app rather than exposing deva.api. Public hosted live compute is outside the release boundary. Reverse-proxy rate limits and resource limits remain deployment responsibilities.
* All prominent historical results and domain limitations remain in the claim ledger and physical-world evidence. No simulation or local confidence interval is promoted to proof. Water and microgrid units/evidence are domain-scoped.
* Existing SVG engineering worlds expose accessible names and exact numeric states. Inputs have labels, buttons are semantic, CSS respects reduced motion, mobile navigation wraps. Full 3D is desktop-oriented; 2D remains available. This is a practical accessibility review, not WCAG certification.
* Existing 10-act stored-data demonstration covers the required research story, including domain switching and explicit negative results. No extra act count is necessary for scientific correctness. The stored ablation and budget negotiation remain inspectable.
* Three.js lazy bundle warning remains visible; software 3D is not advertised as fast. No speculative dependency upgrades or GPU changes.
* No project license was present. Do not invent an owner licence grant. Third-party packages retain their upstream licenses; distribution must retain their notices. Owner licensing remains explicit rather than implied by public hosting.
* Docker daemon access is blocked by the managed sandbox. Container execution remains unvalidated until authorised execution or hosting build; native same-origin production smoke is tested separately.

## Privacy

Bundled observations are synthetic, not real infrastructure sensor data. Local investigations store input configuration, seed, outcomes, events and evidence in .runtime. No conversational memory or telemetry service is introduced. Public mode cannot upload observations or start jobs. Do not load confidential field records into a shared local runtime.

## Outstanding release gates

Current test/build/replay logs and local smoke evidence must be recorded before RC tagging. No canonical public URL or hosting identity is configured. Deployment and actual public smoke testing remain blockers to final release, not reasons to fabricate completion.

Release integration defect found and fixed: starting public and development apps against the same .runtime could let JobStore restart recovery interfere with live development jobs. The observed failed job instead completed in about 63.5 seconds while a clean frontend build was running, exceeding its unchanged 60-second browser deadline; no database-failure diagnosis is claimed for that run. Public serving now uses a dedicated public-archive runtime directory; the release-boundary test checks isolation. This is distinct from scientific solver failure. The initial heavily concurrent browser attempt also retained three startup timeout failures; neither timeout nor assertion was weakened.
