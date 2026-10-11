# Remaining Phase-2 failures

Source: immutable experiment `deva-evolution-415e051c31e3bded`, selected `g2-c012`, cost 532.5578984864775, 13/200 failures. The same split has 44/200 failures for the original cost-399 capacity design. The older 38/200 experiment is separate and unchanged.

`python -m deva.remaining artifacts/evolution-evidence.json --output /tmp/remaining.json` reruns counterfactual diagnosis and solves one-case, capacity-only augmentation LPs with **lower bounds at the selected installed capacities**, existing maximum capacities and the original 700-unit budget. All interventions and numerical outputs are in `artifacts/remaining-failure-analysis.json`.

Six cases are topological disconnections; seven require combined outages and elevated demand. Only three can be repaired by continuous capacity additions within the existing topology, bounds and budget: observed minimum additional costs are approximately 0.217381, 1.650209 and 0.001855 units. Ten have no feasible capacity-only repair under those restrictions. These costs address one opened test case each, not independent generalisation. They do not price new topology or establish construction costs.

The observed hazards are synthetic, uncalibrated and not assigned field plausibility. Availability patterns alone do not establish independent/correlated trigger attribution. Historical capacities contain no lengths, diameters, elevations or source heads, so new hydraulics cannot retrospectively certify or reinterpret these thirteen failures. Hydraulic V2 uses explicit additional geometry and distinct construction-cost assumptions; its results are a new experiment.

This audit deliberately opens the sealed test set for diagnosis. It is excluded from both capacity and hydraulic training/recommendation. No optimiser was changed to memorise the thirteen cases, and no claim of universal superiority or elimination of all failure risk follows.
