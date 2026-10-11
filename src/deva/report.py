"""Portable Markdown report generated exclusively from recorded evidence."""
import argparse
import json
from pathlib import Path
from .audit import verify_hash


def render(envelope):
    verify_hash(envelope);s=envelope['science']
    rows=['# DEVA Engineering Evidence Report','',f"Experiment: `{envelope['experiment_id']}`",'',s['configuration']['objective'],'',
          f"Scientific SHA-256: `{envelope['scientific_sha256']}`",'',
          '## Candidate evidence','', '| Candidate | Generation | Cost | Training failures | Validation failures | Held-out failures | Evidence |',
          '|---|---:|---:|---:|---:|---:|---|']
    for c in s['candidates']:
        if s['schema_version']=='2.0':
            counts=[f"{c[k]['metrics']['failures']}/{c[k]['metrics']['samples']}" for k in ('training','validation','heldout')]
            rows.append(f"| {c['id']} | {c['generation']} | {c['cost']:.3f} | {' | '.join(counts)} | {c['verification']['level']} |")
        else:
            u=c.get('uncertainty',{})
            rows.append(f"| {c['id']} | {c['generation']} | {c['verification'].get('cost','—')} | — | — | {u.get('failures','—')}/{u.get('samples','—')} | {c['verification']['level']} |")
    rows+=['','## Scope and limitations','',*[f'- {l}' for l in s['limitations']],'',
           'No numerical simulation or Monte Carlo result is mathematical or formal verification. Negative results are retained in the full JSON package.','',
           '## Reproduction','',f"Software: `{json.dumps(s['software'],sort_keys=True)}`",'']
    if s['schema_version']=='2.0':
        config=s['experiment_config']
        rows+=['```bash',f"python -m deva.evolve_cli examples/emergency_water.json --seed {config['seed']} --generations {config['generations']} --train-samples {config['train_samples']} --validation-samples {config['validation_samples']} --test-samples {config['test_samples']} --output replay.json",'```','',
               'Use the exact `science.configuration` from the package when it differs from the example. Seed streams, every failure, sensitivities, attack witnesses and provenance are preserved in the JSON.']
    return '\n'.join(rows)+'\n'


def main():
    p=argparse.ArgumentParser();p.add_argument('evidence',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    a.output.write_text(render(json.loads(a.evidence.read_text())))
if __name__=='__main__':main()
