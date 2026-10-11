# Failure taxonomy — derived from preserved evidence

Source: `deva-9a473107d6fcb70f`; original artifact SHA-256 `14e632693c8f4b9549bb326310715f719b068da373a2feeae1c9d641378ecd5e`. The original 38/200 failures and original artifact are unchanged. `artifacts/baseline-failure-analysis.json` contains all failed scenario IDs and counterfactual results.

Observed categories (labels overlap):
* **Outage–demand interaction: 36 cases.** Each outage-only, demand-only and supply-only counterfactual passes, but their combination fails. Restoring pipes or nominal demand rescues service. Nominal-demand outage synthesis allocates exactly 95% service through the surviving path; it has no headroom for simultaneous demand growth. This is a missing cross-scenario requirement, not evidence of deliberate optimiser misconduct.
* **Topological disconnection: 2 cases** (`heldout:00005`, `heldout:00198`). Multiple lost edges leave a demand node unreachable from every usable source. Additional capacity on the same topology cannot restore that connection.
* Demand-only insufficiency, supply-only insufficiency and outage-only capacity insufficiency do **not** occur for this candidate in this sample. They remain supported diagnostic labels for other designs.

Failed-edge involvement: west-trunk 9, east-trunk 10, west-hospital 9, west-shelter 10, east-hospital 7, east-shelter 9. These counts overlap and are not component failure probabilities. Pearson association with binary failure: unavailable-edge count ≈0.771, global demand ≈0.085, global supply ≈−0.037. Associations alone conceal the strong conditional outage–demand interaction; counterfactuals supply the stronger model-based diagnosis.

The original generator varies only global demand, not hospital/shelter-specific patterns. It has no temporal state: no cascade, independence of consecutive time events, recovery or repair claim is possible. Corridor patterns are consistent with correlated failures but cannot identify the originating trigger because the original package records availability, not generator event labels. No retroactive trigger attribution is invented.

Diagnosis reruns six controlled counterfactuals per failed case and graph reachability. Labels record computational evidence within the abstract capacity model; they are not causal field conclusions. Failure history is append-only across experiment packages.
