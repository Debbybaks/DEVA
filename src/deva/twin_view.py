"""One-way projection of stored twin computation into the existing scientific world."""
from .audit import verify_hash
from .hydraulic_view import render_problem,state
from .hydraulic_v2 import simulate
from .hydraulic_evidence import audit


def project(record):
    verify_hash(record)
    s=record['science'];raw=s['configuration'];d=s['diameters_m'];model=s['digital_twin']['estimated_model']
    frames=[]
    for label,rows in s['calibration']['rows'].items():
        conditions={row['observation']['scenario']['id']:row['observation']['scenario'] for row in rows}
        for scenario in conditions.values():
            a=simulate(raw,d,scenario);b=simulate(model,d,scenario)
            audit(raw,d,scenario,a);audit(model,d,scenario,b)
            frames.append(dict(id=scenario['id'],split=label,timestamp=next(r['observation']['timestamp'] for r in rows if r['observation']['scenario']['id']==scenario['id']),baseline=state(raw,d,scenario,a),estimated=state(model,d,scenario,b),observations=[r for r in rows if r['observation']['scenario']['id']==scenario['id']]))
    cascade=[dict(index=f['index'],time_seconds=f['time_seconds'],state=state(model,d,f['scenario'],f['result']),hazards=f['hazards'],events=f['events'],newly_failed=f.get('newly_failed',[]),restored=f.get('restored',[])) for f in s['cascade']['frames']]
    proof=s['engineering_agent']['science']['outputs'].get('verify_property',{})
    return dict(experiment_id=record['experiment_id'],scientific_sha256=record['scientific_sha256'],label=s['dataset']['label'],problem=render_problem(raw),frames=frames,cascade=cascade,causal_graph=s['cascade']['causal_graph'],cascade_events=s['cascade']['events'],ensemble=dict(time_seconds=s['ensemble']['time_seconds'],service_percentiles=s['ensemble']['service_percentiles'],terminal_failures=s['ensemble']['terminal_failures'],samples=s['ensemble']['samples'],trajectories=[[f['result']['service_fraction'] for f in t['frames']] for t in s['ensemble']['trials']],scope=s['ensemble']['scope']),calibration={k:s['calibration'][k] for k in ('status','parameters','metrics','initial_identifiability','fitted_identifiability','covariance','searches','acceptance_criteria','uncertainty_scope')},incremental_calibration=s['incremental_calibration'],sensor_placement=s['sensor_placement'],claim_ledger=s['claim_ledger'],provenance_graph=s['provenance_graph'],engineering_agent=s['engineering_agent']['science'],verification=proof,knowledge_states=s['digital_twin']['states'],limitations=s['limitations'],code=s['code'],seed=s['seed'])
