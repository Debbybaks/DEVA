"""Professional Markdown evidence report from a hash-validated stored twin."""
import argparse,json
from pathlib import Path
from deva.audit import verify_hash
p=argparse.ArgumentParser();p.add_argument('evidence');p.add_argument('--output',required=True);a=p.parse_args()
e=json.loads(Path(a.evidence).read_text());verify_hash(e);s=e['science'];c=s['calibration'];agent=s['engineering_agent']['science']
lines=['# DEVA synthetic digital-twin Engineering Evidence Package','',s['configuration']['objective'],'',f"Experiment: `{e['experiment_id']}`",f"Scientific SHA256: `{e['scientific_sha256']}`",'','## Scientific scope','','Synthetic hidden-parameter recovery with held-out observation validation. No field calibration or real-world rupture prediction claimed. Historical 38/200 and 44/200 → 13/200 experiments remain separate and immutable.','','## Observations and mathematical model','','Pressure-dependent service, fixed-friction Darcy–Weisbach head loss, signed flow, conservation, prescribed source heads and independent numerical audits. Observation units: pressure head m; signed flow m³/s; known independent Gaussian noise. Five calibration epochs / 20 measurements, four withheld epochs / 16 measurements.','','## Calibration and identifiability','',f"Status: {c['status']}; local sensitivity rank {c['fitted_identifiability']['rank']}/{c['fitted_identifiability']['parameters']}.",'']
for par,truth in zip(c['parameters'],s['dataset']['ground_truth']):
 lines.append(f"- {par['id']}: initial {par['initial']}, estimate {par['estimate']:.8f}, ground truth {truth}, local standard error {par['standard_error']}; unit {par['unit']}.")
lines+=['','```json',json.dumps(c['metrics'],indent=2),'```','',c['uncertainty_scope'],'','## Observation design','',f"Recommended two-sensor layout: {', '.join(s['sensor_placement']['recommendation'])}.",s['sensor_placement']['scope'],'',f"Given {s['next_observation']['current_sensors']}, highest conditional information-gain recommendation: {s['next_observation']['value_of_information'][0]}.",'','## Research-hazard cascade','','λ = λ₀(1+d) + λs(1+d)[max(0,p/pref−1)² + max(0,|v|/vref−1)²]. Interval event probability = 1−exp(−λΔt). Coefficients uncalibrated; closure approximates isolation, not leakage/fracture physics.']
for event in s['cascade']['events']:
 h=event['trigger'];lines.append(f"- {event['simulation_time_seconds']} s: {event['component']} failure; probability {h['probability']:.8f}, recorded draw {h['uniform_draw']:.8f}, hazard change {h['hazard_change']:.8f} s⁻¹; resulting service {event['resulting_state']['service_fraction']:.6f}.")
lines+=['','## Autonomous engineering investigation','',f"Stopping reason: {agent['stopping_reason']}",f"Selected candidate: {agent['selection']}; requested target achieved: {agent['target_achieved']}.",'']
for candidate in agent['outputs']['simulate_training']['candidates']:
 lines.append(f"- {candidate['id']}: cost {candidate['cost']:.6f}; training failures {candidate['training']['failures']}/{candidate['training']['samples']}; rejection {candidate['rejection_reason']}; mutation {candidate['mutation']}.")
lines+=['']+[r['text'] for r in agent['research_narrative']]+['','## Property-specific proof scope','']
for obj in agent['outputs']['verify_property']['objects']:
 lines+=[f"- {obj['requirement_id']}: {obj['status']} / {obj['result']}; {obj['property']}; {obj['scope']}. Proof SHA256 {obj.get('proof_sha256')}; counterexample {obj.get('counterexample_closed')}."]
lines+=['','## Scientific claim ledger','']
for claim in s['claim_ledger']:
 lines+=[f"- {claim['claim']} Evidence: science/{claim['evidence']}; status {claim['status']}; limitations: {' '.join(claim['limitations'])}"]
lines+=['','## Limitations','']+[f'- {l}' for l in s['limitations']+s['cascade']['limitations']]+['','## Reproduction','','```bash',f".venv/bin/python -m deva.digital_twin examples/emergency_water_hydraulic.json --seed {s['seed']} --output /tmp/twin-replay.json",'.venv/bin/python scripts/replay_history.py','```','',f"Use scientific source revision `{s['code']['git_revision']}`; source fingerprint `{s['code']['scientific_source_sha256']}`.",'Software: '+json.dumps(s['software']), 'Compare science payload and SHA256; timestamps/performance measurements are excluded. Independent seeds, all observations, rejected candidates, solver evaluations, policies, draws, cascade frames and proof objects are in the JSON package.']
Path(a.output).write_text('\n'.join(lines)+'\n')
