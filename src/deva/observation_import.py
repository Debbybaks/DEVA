"""Domain-scoped observation ingestion; missing measurements remain quality evidence."""

from datetime import datetime
from .units import Quantity


def import_batch(payload, domain_id, quantities, components):
    required = {"domain", "provenance", "records"}
    if set(payload) != required or payload["domain"] != domain_id:
        raise ValueError("Domain-scoped observation batch required")
    provenance = payload["provenance"]
    if (
        set(provenance) != {"kind", "source"}
        or provenance["kind"] not in ["SYNTHETIC", "REFERENCE", "FIELD"]
        or not provenance["source"]
    ):
        raise ValueError("Explicit observation provenance required")
    if (
        not isinstance(payload["records"], list)
        or not 1 <= len(payload["records"]) <= 10000
    ):
        raise ValueError("Bounded observation records required")
    seen = set()
    accepted = []
    missing = []
    for record in payload["records"]:
        if set(record) != {
            "id",
            "timestamp",
            "component",
            "sensor",
            "quantity",
            "measurement",
            "uncertainty",
            "split",
        }:
            raise ValueError("Exact observation fields required")
        if (
            any(
                not isinstance(record[k], str) or not record[k]
                for k in ["id", "timestamp", "component", "sensor", "quantity", "split"]
            )
            or record["id"] in seen
        ):
            raise ValueError("Unique observation identities required")
        seen.add(record["id"])
        stamp = datetime.fromisoformat(record["timestamp"].replace("Z", "+00:00"))
        if (
            stamp.tzinfo is None
            or record["component"] not in components
            or not record["sensor"]
            or record["quantity"] not in quantities
            or record["split"] not in ["calibration", "validation", "heldout"]
        ):
            raise ValueError(
                "Known component/quantity, timezone and explicit split required"
            )
        if record["measurement"] is None:
            missing.append(
                dict(record=record, reason="MISSING MEASUREMENT; no zero imputation")
            )
            continue
        unit = quantities[record["quantity"]]
        q = record["measurement"]
        sigma = record["uncertainty"]
        if any(
            not isinstance(v, dict)
            or set(v) != {"value", "unit"}
            or not isinstance(v["unit"], str)
            for v in [q, sigma]
        ):
            raise ValueError(
                "Explicit numeric measurement/uncertainty quantity required"
            )
        value = Quantity.of(q["value"], q["unit"]).to(unit)
        uncertainty = Quantity.of(sigma["value"], sigma["unit"]).to(unit)
        if uncertainty <= 0:
            raise ValueError("Positive measurement uncertainty required")
        accepted.append(
            dict(
                **record,
                canonical_value=value,
                canonical_uncertainty=uncertainty,
                canonical_unit=unit,
                provenance=provenance,
                domain=domain_id,
            )
        )
    sensors = {
        r["sensor"]: dict(component=r["component"], quantity=r["quantity"])
        for r in accepted
    }
    for sensor in sensors:
        if (
            len(
                {
                    (r["component"], r["quantity"])
                    for r in accepted
                    if r["sensor"] == sensor
                }
            )
            != 1
        ):
            raise ValueError(
                "Sensor identity cannot silently change physical quantity/component"
            )
    return dict(
        domain=domain_id,
        provenance=provenance,
        accepted=accepted,
        missing=missing,
        sensors=sensors,
        quality=dict(total=len(seen), accepted=len(accepted), missing=len(missing)),
        status="INGESTED / NOT CALIBRATED",
        limitations=[
            "Import is not calibration or validation",
            "Missing measurements are retained and excluded without imputation",
        ],
    )
