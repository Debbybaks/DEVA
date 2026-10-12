# Observation import and field-calibration readiness

`deva.observation_import.import_batch` accepts an explicit domain identity, declared quantity-unit map and known component IDs. Records carry unique ID, timezone-aware timestamp, component, sensor, quantity, dimension-checked measurement and positive uncertainty, and explicit calibration/validation/held-out split. Provenance is SYNTHETIC, REFERENCE or FIELD with a source; the importer never changes it to a stronger status.

Missing measurements are retained with a quality reason and excluded without zero imputation. Sensor identities cannot silently change quantity/component. The output is INGESTED / NOT CALIBRATED; import alone establishes neither calibration nor physical validity. The caller must supply its domain's schema and an independently reviewed splitting policy. Field sensor bias, correlated noise, authentication, streaming quality control and automatic water-calibration conversion remain outside this bounded importer.

`examples/synthetic_observation_import.json` is a reproducible synthetic example, including one missing record. No field data or real-world calibration was fabricated. Existing water calibration observations remain supported by their original strict schema.
