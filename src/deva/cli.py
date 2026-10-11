import argparse
import json
from pathlib import Path
from .experiment import run


def main():
    parser = argparse.ArgumentParser(description='DEVA reproducible capacity-network experiment')
    parser.add_argument('problem', type=Path)
    parser.add_argument('--seed', type=int, default=20261011)
    parser.add_argument('--samples', type=int, default=200)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.problem.stat().st_size > 1_000_000:
            raise ValueError('Problem file exceeds 1 MB')
        def reject_duplicates(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError(f'Duplicate JSON key: {key}')
                result[key] = value
            return result
        raw = json.loads(args.problem.read_text(), object_pairs_hook=reject_duplicates)
        evidence = run(raw, args.seed, args.samples)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(evidence, indent=2, allow_nan=False)+'\n')
    except (ValueError, OSError, RuntimeError) as error:
        parser.exit(2, f'DEVA experiment failed: {error}\n')
    print(json.dumps(dict(experiment_id=evidence['experiment_id'], winner=evidence['science']['winner'], evidence=str(args.output))))


if __name__ == '__main__':
    main()
