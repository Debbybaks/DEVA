"""Predeclared larger catalogue search without relaxing engineering constraints."""

import gzip, json
from pathlib import Path
from deva.general_engineer import investigate
from deva.domains.water import WaterDomain
from deva.domains.microgrid import MicrogridDomain

results = []
for domain, budget in [
    (
        WaterDomain(
            json.loads(Path("examples/emergency_water_hydraulic.json").read_text())
        ),
        500,
    ),
    (MicrogridDomain(json.loads(Path("examples/microgrid.json").read_text())), 300),
]:
    e = investigate(
        domain,
        seed=20261210,
        maximum_cost=budget,
        maximum_simulations=1500,
        maximum_candidates=64,
        maximum_generations=8,
        training_samples=16,
        validation_samples=32,
        heldout_samples=120,
    )
    results.append(e)
    print(
        domain.descriptor["id"],
        len(e["science"]["candidates"]),
        e["science"]["solver_calls"],
        e["science"]["heldout"]["failures"] if e["science"]["heldout"] else "UNTESTED",
        e["science"]["stopping_reason"],
    )
with gzip.open("artifacts/phase5-scale-search.json.gz", "wt") as f:
    json.dump(results, f, allow_nan=False)
