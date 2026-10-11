import argparse
import json
from pathlib import Path
from .evolution import evolve


def main():
    p = argparse.ArgumentParser(description="DEVA design evolution experiment")
    p.add_argument("problem", type=Path)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--seed", type=int, default=20261013)
    p.add_argument("--generations", type=int, default=3)
    p.add_argument("--train-samples", type=int, default=60)
    p.add_argument("--validation-samples", type=int, default=80)
    p.add_argument("--test-samples", type=int, default=200)
    a = p.parse_args()
    result = evolve(
        json.loads(a.problem.read_text()),
        a.seed,
        a.generations,
        a.train_samples,
        a.validation_samples,
        a.test_samples,
    )
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(
        json.dumps(
            dict(
                experiment_id=result["experiment_id"],
                recommendation=result["science"]["recommendation"],
                candidates=len(result["science"]["candidates"]),
            )
        )
    )


if __name__ == "__main__":
    main()
