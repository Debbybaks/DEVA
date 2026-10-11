"""Reproducible synthetic observations and explicit digital-twin knowledge states."""
from datetime import datetime, timedelta, timezone
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import numpy as np
from .calibration import apply, predict, observations, calibrate, sensor_placement, VERSION
from .hydraulic_v2 import parse, simulate
from .hydraulic_evidence import audit, envelope, provenance_revision
from .experiment import canonical


def benchmark_data(raw, diameters, seed=20261030, noise=True):
    """Truth is returned for evaluation but never supplied to the estimation tool."""
    m = parse(raw)
    specs = [dict(id='west-resistance', kind='friction_multiplier', components=[p['id'] for p in m['pipes'] if p['corridor']=='west'], initial=1., lower=.5, upper=1.8), dict(id='east-resistance', kind='friction_multiplier', components=[p['id'] for p in m['pipes'] if p['corridor']=='east'], initial=1., lower=.5, upper=1.8), dict(id='demand-coefficient', kind='demand_multiplier', components=[n['id'] for n in m['nodes'] if n['demand']>0], initial=1., lower=.7, upper=1.4)]
    truth = [1.25, .85, 1.08]
    streams = np.random.SeedSequence(seed).spawn(2)
    splits = {}
    sensors = [('hospital-pressure', 'hospital', 'pressure', .08), ('shelter-pressure','shelter','pressure',.08), ('west-meter','west-trunk','flow',.00004), ('east-meter','east-trunk','flow',.00004)]
    for split, count, stream in [('calibration',5,streams[0]),('validation',4,streams[1])]:
        rng = np.random.default_rng(stream)
        records = []
        for t in range(count):
            scenario = dict(id=f'{split}:{t}', demand_factor=float(rng.uniform(.9,1.45)), source_head_delta_m=float(rng.uniform(-7,2)))
            timestamp = (datetime(2026,10,1,tzinfo=timezone.utc)+timedelta(hours=t+(0 if split=='calibration' else 24))).isoformat()
            for sensor,component,kind,sigma in sensors:
                unit = 'm' if kind=='pressure' else 'm3/s'
                records.append(dict(id=f'{split}:{t}:{sensor}', timestamp=timestamp, sensor_id=sensor, component=component, measurement_type=kind, measurement=dict(value=0.,unit=unit), uncertainty=dict(value=sigma,unit=unit), scenario=scenario, provenance=dict(kind='SYNTHETIC',source=f'hidden-parameter-benchmark:{seed}',noise='independent Gaussian, known standard deviation',split=split)))
        normalized = observations(raw,records)
        values = predict(raw,diameters,specs,truth,normalized)
        for r,v in zip(records,values):
            r['measurement']['value'] = float(v + (rng.normal(0,r['uncertainty']['value']) if noise else 0))
        splits[split]=records
    return dict(parameters=specs, ground_truth=truth, splits=splits, seed=seed, diameters_m=diameters, label='SYNTHETIC HIDDEN-PARAMETER BENCHMARK', truth_model='Same hydraulic equations as estimator; validates parameter recovery, not structural model adequacy or field reality')


def twin_states(raw, diameters, calibration):
    """No observation is silently promoted to an estimate or forecast."""
    specs=[{k:p[k] for k in ('id','kind','components','initial','lower','upper')} for p in calibration['parameters']]
    values=[p['estimate'] for p in calibration['parameters']]
    estimated=apply(raw,specs,values)
    states=[]
    for split,rows in calibration['rows'].items():
        for row in rows:
            r=row['observation']; base=dict(component=r['component'],quantity=r['measurement_type'],unit=r['canonical_unit'],timestamp=r['timestamp'],observation_id=r['id'])
            states.append(dict(**base,category='OBSERVED',value=r['value_si'],uncertainty=r['sigma_si'],provenance=r['provenance']))
            states.append(dict(**base,category='ESTIMATED',value=row['prediction'],uncertainty=float(np.sqrt(row['parameter_variance'])) if row['parameter_variance'] is not None else None,provenance=dict(calibration_status=calibration['status'],split=split,model_version=VERSION),residual=row['residual']))
    condition=dict(id='forecast:unseen-demand',demand_factor=1.5,source_head_delta_m=-5.)
    result=simulate(estimated,diameters,condition); audit(estimated,diameters,condition,result)
    for n,v in result['pressure_head_m'].items():
        states.append(dict(component=n,quantity='pressure',unit='m',timestamp='2026-10-03T00:00:00+00:00',category='FORECAST' if v is not None else 'UNKNOWN',value=v,uncertainty=None,provenance=dict(scenario=condition,model_version=VERSION,scope='Conditional forecast, not observed future')))
    nominal=simulate(raw,diameters,{'id':'unfitted-nominal'})
    for n,v in nominal['pressure_head_m'].items():
        states.append(dict(component=n,quantity='pressure',unit='m',timestamp=None,category='SIMULATED' if v is not None else 'UNKNOWN',value=v,uncertainty=None,provenance=dict(scenario='unfitted-nominal',scope='Original uncalibrated model')))
    return dict(states=states,estimated_model=estimated,forecast=dict(scenario=condition,result=result),categories=['OBSERVED','ESTIMATED','SIMULATED','FORECAST','UNKNOWN'],scope='Synthetic offline digital twin; no live field ingestion or state-filter claim')


def incremental(raw, diameters, dataset):
    """Prefix refits with new observations; known timestamps, no real-time claim."""
    records=dataset['splits']['calibration']
    times=sorted({r['timestamp'] for r in records})
    out=[]
    for count in (1,3,len(times)):
        prefix=[r for r in records if r['timestamp'] in times[:count]]
        fitted=calibrate(raw,diameters,dataset['parameters'],prefix,dataset['splits']['validation'],seed=dataset['seed'],starts=1)
        out.append(dict(observation_count=len(prefix),timestamp=times[count-1],status=fitted['status'],parameters=fitted['parameters'],identifiability=fitted['fitted_identifiability'],metrics=fitted['metrics'],scope='Independent prefix refit; held-out set never used for parameter fitting'))
    return out


def experiment(raw, diameters, seed=20261030, progress=None):
    import platform, scipy, time
    started=time.perf_counter()
    if progress: progress('observations',{})
    dataset=benchmark_data(raw,diameters,seed)
    if progress: progress('calibration',dict(observations=len(dataset['splits']['calibration'])))
    fitted=calibrate(raw,diameters,dataset['parameters'],dataset['splits']['calibration'],dataset['splits']['validation'],seed=seed)
    errors=[p['estimate']-v for p,v in zip(fitted['parameters'],dataset['ground_truth'])]
    if progress: progress('sensor-placement',{})
    design=sensor_placement(raw,diameters,dataset['parameters'],[p['estimate'] for p in fitted['parameters']],dataset['splits']['calibration'],budget=2)
    twin=twin_states(raw,diameters,fitted)
    if progress: progress('cascade',{})
    from .rupture import cascade, ensemble, policies
    model=twin['estimated_model']; policy=policies(model)
    cascade_result=cascade(model,diameters,dict(id='research-initiator',closed=['east-trunk']),policy,seed=seed+10)
    futures=ensemble(model,diameters,dict(id='research-initiator',closed=['east-trunk']),policy,seed=seed+11,count=12)
    if progress: progress('engineering-agent',{})
    from .engineering_agent import investigate
    objective=dict(component='hospital',maximum_failure_probability=.02,maximum_cost_increase=.12,training_samples=12,validation_samples=40,maximum_candidates=7,maximum_tool_calls=10,seed=seed+20)
    agent=investigate(raw,diameters,objective,calibration_data=dict(parameters=dataset['parameters'],calibration=dataset['splits']['calibration'],validation=dataset['splits']['validation']))
    agent={k:v for k,v in agent.items() if k!='timestamp'}
    ledger=[dict(id='C-CALIBRATION',claim=f"Held-out pressure RMSE {fitted['metrics']['validation']['rmse_by_quantity']['pressure']:.6f} m under the synthetic benchmark.",evidence='calibration/rows/validation',status=fitted['status'],assumptions=['Same hydraulic equations generate synthetic truth; independent known Gaussian noise.'],limitations=['Not field calibration or external validation.'],reproduction_route='deva.digital_twin.experiment with stored model, diameters and seed'),dict(id='C-IDENTIFIABILITY',claim=f"Local sensitivity rank {fitted['fitted_identifiability']['rank']}/{len(dataset['parameters'])}.",evidence='calibration/fitted_identifiability',status='NUMERICAL IDENTIFIABILITY',assumptions=['Declared excitation and finite-difference scales.'],limitations=['Not a global uniqueness proof.'],reproduction_route='deva.calibration.jacobian'),dict(id='C-CASCADE',claim=f"{len(cascade_result['events'])} research-hazard failures in the selected seeded trajectory.",evidence='cascade/events',status='UNCALIBRATED RESEARCH HAZARD',assumptions=['Declared hazard law and quasi-steady redistribution.'],limitations=cascade_result['limitations'],reproduction_route='deva.rupture.cascade with stored policy and seed')]
    graph=dict(nodes=[dict(id='observations',kind='SYNTHETIC DATA',reference='dataset/splits'),dict(id='model',kind='HYDRAULIC MODEL',reference='configuration'),dict(id='fit',kind='CALIBRATION',reference='calibration'),dict(id='validation',kind='HELD-OUT VALIDATION',reference='calibration/rows/validation'),dict(id='cascade',kind='RESEARCH HYPOTHESIS',reference='cascade'),*[dict(id=c['id'],kind='CLAIM',reference='claim_ledger/'+str(i)) for i,c in enumerate(ledger)]],edges=[dict(source='observations',target='fit'),dict(source='model',target='fit'),dict(source='fit',target='validation'),dict(source='validation',target='C-CALIBRATION'),dict(source='fit',target='C-IDENTIFIABILITY'),dict(source='fit',target='cascade'),dict(source='cascade',target='C-CASCADE')])
    science=dict(schema_version='4.0',model_version=VERSION,configuration=raw,diameters_m=diameters,seed=seed,dataset=dataset,calibration=fitted,truth_evaluation=dict(parameter_errors=errors,relative_errors=[e/v for e,v in zip(errors,dataset['ground_truth'])],scope='Truth unsealed only after fitting; all model discrepancy absent by construction'),digital_twin=twin,sensor_placement=design,cascade=cascade_result,ensemble=futures,engineering_agent=agent,claim_ledger=ledger,provenance_graph=graph,incremental_calibration=incremental(raw,diameters,dataset),code=provenance_revision(),software=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__),limitations=['Synthetic data generated with same equations; no field calibration or independent physical validity established.','Local sensitivity rank does not prove global parameter uniqueness.','Gaussian independent noise and known excitation assumed; sensor bias and correlated noise unmodelled.','Local linearised prediction intervals exclude structural model error.','Research rupture hazard, if evaluated separately, is uncalibrated; real-world rupture prediction remains unmodelled.'])
    result=envelope(science)
    result['experiment_id']='deva-twin-'+result['scientific_sha256'][:16]
    result['performance']=dict(runtime_seconds=time.perf_counter()-started,scope='Measured wall clock, excluded from scientific hash')
    return result


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('problem');p.add_argument('--seed',type=int,default=20261030);p.add_argument('--output',required=True)
    a=p.parse_args();raw=json.loads(Path(a.problem).read_text())
    e=experiment(raw,[.125]*len(raw['pipes']),a.seed)
    Path(a.output).write_text(json.dumps(e,indent=2,allow_nan=False))
    print(json.dumps(dict(experiment_id=e['experiment_id'],status=e['science']['calibration']['status'],metrics=e['science']['calibration']['metrics'])))
