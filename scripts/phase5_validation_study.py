"""Retained population, assumption-sensitivity, sensor-layout and proof evidence."""

import gzip, json, hashlib, resource
from pathlib import Path
from deva.audit import verify_hash
from deva.experiment import canonical
from deva.provenance import source_revision
from deva.domains.water import WaterDomain
from deva.domains.microgrid import MicrogridDomain
from deva.domains.energy_certificate import certificate
from deva.population import evaluate_population
from deva.hypotheses import update
import numpy as np

with gzip.open("artifacts/phase5-search-evidence.json.gz", "rt") as f:
    research = json.load(f)
verify_hash(research)
results = []
timings = {}
assumptions = []
for kind, cls, filename in [
    ("water", WaterDomain, "emergency_water_hydraulic.json"),
    ("microgrid", MicrogridDomain, "microgrid.json"),
]:
    e = next(
        e["science"]
        for e in research["science"]["experiments"]
        if e["science"]["domain"]["id"] == kind and e["science"]["strategy"] == "hybrid"
    )
    chosen = next(c for c in e["candidates"] if c["id"] == e["selection"])
    domain = cls(json.loads(Path("examples/" + filename).read_text()))
    population = evaluate_population(domain, chosen["design"], 20261201, 512)
    timings[kind] = population.pop("performance")
    results.append(population["science"])
    if kind == "microgrid":
        for efficiency in [0.8, 0.9, 1.0]:
            raw = json.loads(Path("examples/" + filename).read_text())
            raw["discharge_efficiency"] = efficiency
            r = evaluate_population(
                MicrogridDomain(raw), chosen["design"], 20261202, 32
            )
            r["science"]["assumed_discharge_efficiency"] = efficiency
            assumptions.append(r["science"])
raw = json.loads(Path("examples/microgrid.json").read_text())
raw.update(
    demand=[dict(value=10, unit="kW")] * 2,
    solar_profile=[0, 0],
    initial_soc=1,
    discharge_efficiency=1,
)
proof = certificate(
    MicrogridDomain(raw),
    [0, 36000000, 10000],
    dict(id="independent-two-hour-bound", generator_outages=[0, 1]),
)
twin = json.loads(Path("artifacts/digital-twin-evidence.json").read_text())
verify_hash(twin)
layouts = [
    x for x in twin["science"]["sensor_placement"]["layouts"] if len(x["sensors"]) == 2
]
rng = np.random.default_rng(20261203)
random = [layouts[int(rng.integers(len(layouts)))] for _ in range(32)]
sensors = dict(
    domain="water",
    source_experiment=twin["experiment_id"],
    seed=20261203,
    recommended=twin["science"]["sensor_placement"]["recommendation"],
    best_information_score=max(x["information_score"] for x in layouts),
    random_scores=[x["information_score"] for x in random],
    random_mean=float(np.mean([x["information_score"] for x in random])),
    scope="Local identifiability/log-det information proxy; not field failure detection or global parameter recovery",
)
comparison = [
    x
    for x in research["science"]["ablation"]
    if x["domain"] == "microgrid" and x["strategy"] in ["guided", "random"]
]
h = dict(
    id="H-GUIDANCE-MICROGRID",
    domain="microgrid",
    statement="Guided search improves mean held-out failure relative to random in this declared bounded study",
    status="PROPOSED",
)
h = update(h, "TESTING", [])
h = update(
    h,
    "WEAKENED",
    [
        dict(
            domain="microgrid",
            reference=research["experiment_id"] + "/science/ablation",
            scope="Three fixed seeds: guided mean failure exceeds random; exploratory, no statistical superiority conclusion",
        )
    ],
)
science = dict(
    source_research=research["experiment_id"],
    source_sha256=research["scientific_sha256"],
    code=source_revision(),
    populations=results,
    assumption_sweeps=assumptions,
    energy_certificate=proof,
    sensor_comparison=sensors,
    hypotheses=[h],
    limitations=[
        "Larger synthetic populations do not establish field validity",
        "Efficiency sweep is assumption sensitivity, not a calibrated probability distribution",
        "No valid real-world rupture dataset is available; research hazard status retained",
    ],
)
digest = hashlib.sha256(canonical(science).encode()).hexdigest()
envelope = dict(
    experiment_id="deva-phase5-validation-" + digest[:16],
    scientific_sha256=digest,
    science=science,
    performance=dict(
        populations=timings,
        peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
    ),
)
with gzip.open("artifacts/phase5-validation-study.json.gz", "wt") as f:
    json.dump(envelope, f, allow_nan=False)
print(
    envelope["experiment_id"],
    [(x["domain"], x["failures"], x["count"]) for x in results],
    timings,
)
