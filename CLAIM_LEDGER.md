# Scientific Claim Ledger

The hydraulic evidence package contains machine-readable `science.claim_ledger`. Each entry specifies the sentence, status, supporting evidence paths, assumptions, limitations and reproduction route. The current entries cover declared hydraulic requirements, independent held-out failure observations and bounded topology connectivity. The failure count statement carries a Wilson interval. The formal statement refers to its exact verification object and remains separate from numerical hydraulic service.

Evidence Mode renders these objects directly and exposes source revision/fingerprint, seeds, full JSON, SMT-LIB and proof text or counterexample. The browser does not generate explanatory claims with an LLM. Interactive failure traces list imposed outages, computed disconnections/pressures, delivered service and actual violated requirements. They are explicitly observed linked facts, not proof of unique causal attribution or propagation time.

CLI reproduction: `python -m deva.hydraulic_experiment examples/emergency_water_hydraulic.json --seed 20261020 --output /tmp/hydraulic.json`. The code object records the last Git commit affecting `src/deva`, whether those sources were dirty, and the SHA-256 of the sorted Python source contents. Documentation/UI-only commits therefore do not alter scientific identity. Reproduction requires matching source fingerprint and pinned numerical/formal solver versions. The full envelope's timestamp is excluded from the canonical science hash.

Claims from old capacity experiments remain unchanged and scoped to their old model. A new pressure result cannot retroactively certify them. Development experiment snapshots are retained separately, compressed without discarding outputs; the current committed experiment points to clean scientific sources.

## Phase-4 claim objects

The separate digital-twin package records claims C-CALIBRATION (held-out synthetic pressure error), C-IDENTIFIABILITY (local sensitivity rank) and C-CASCADE (recorded research-hazard events). Every claim carries an evidence path, status, assumptions, limitations and reproduction route. The autonomous investigation separately records finite-sample component-service claims, structured critique and exact tool-output hashes. The world exposes these via a claim/data/model/validation evidence graph. No calibration or cascade claim inherits bounded topology verification status.
