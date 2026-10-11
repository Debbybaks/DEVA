"""Bounded multi-objective evolution with retained ancestry and sealed test draws."""
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import platform
import numpy as np
import scipy
from .schema import Problem
from .model import Scenario, simulate, synthesise, TOL
from .scenarios import declared, sampled, DISTRIBUTION
from .analysis import metrics, diagnose, sensitivity
from .verification import verify, wilson
from .adversary import discover
from .experiment import canonical
from .audit import audit_result

EVOLUTION_VERSION='capacity-evolution-0.2.0'


def pareto_front(candidates):
    eligible=[c for c in candidates if c['verification']['requirements_pass']]
    def objectives(c):return [c['cost'],c['training']['metrics']['failure_rate'],c['training']['metrics']['mean_unmet_m3h']]
    output=[]
    for c in eligible:
        a=np.array(objectives(c))
        if not any(np.all(np.array(objectives(other))<=a+1e-9) and np.any(np.array(objectives(other))<a-1e-9) for other in eligible if other['id']!=c['id']):
            output.append(c['id'])
    return sorted(output)


def provenance_graph(p,candidates,scenarios,recommendation):
    nodes=[dict(id='requirement:service',kind='requirement',label=f'Per-node service ≥ {p.target}'),
           dict(id='requirement:budget',kind='requirement',label=f'Budget ≤ {p.budget}'),
           dict(id='assumption:recourse',kind='assumption',label='Steady-state perfect adaptive dispatch'),
           dict(id='model:capacity',kind='model',label='Conservation and capacity LP'),
           dict(id='conclusion:recommendation',kind='conclusion',label=recommendation or 'No surviving candidate')]
    links=[dict(source='assumption:recourse',target='model:capacity',relation='limits')]
    for split,ss in scenarios.items():
        nodes.extend(dict(id=f'scenario:{split}:{s.id}',kind='scenario',label=s.id,split=split) for s in ss)
    for c in candidates:
        cid=f'candidate:{c["id"]}'
        nodes.append(dict(id=cid,kind='candidate',label=c['id']))
        links.append(dict(source='model:capacity',target=cid,relation='models'))
        for parent in c['parents']:links.append(dict(source=f'candidate:{parent}',target=cid,relation='mutated_into'))
        vid=f'verification:{c["id"]}'
        nodes.append(dict(id=vid,kind='verification',label=c['verification']['level']))
        links.extend([dict(source='requirement:service',target=vid,relation='checked_by'),dict(source='requirement:budget',target=vid,relation='checked_by')])
        for split in ('declared','training','validation','heldout'):
            results=c.get(split,{}).get('results',[])
            for r in results:
                rid=f'result:{c["id"]}:{split}:{r["scenario_id"]}'
                nodes.append(dict(id=rid,kind='simulation' if r['passes'] else 'failure',label=f'{split}: {r["service_fraction"]:.4f}',candidate_id=c['id'],split=split,scenario_id=r['scenario_id']))
                links.extend([dict(source=cid,target=rid,relation='evaluated'),dict(source=f'scenario:{split}:{r["scenario_id"]}',target=rid,relation='input')])
                if split=='declared':links.append(dict(source=rid,target=vid,relation='supports'))
        if c['id']==recommendation:
            links.append(dict(source=vid,target='conclusion:recommendation',relation='scoped_evidence'))
            links.append(dict(source=cid,target='conclusion:recommendation',relation='training_selected'))
    return dict(nodes=nodes,edges=links)


def evolve(raw,seed=20261013,generations=3,train_samples=60,validation_samples=80,test_samples=200,progress=None):
    if isinstance(generations,bool) or not isinstance(generations,int) or not 1<=generations<=8:
        raise ValueError('Require 1–8 generations')
    if any(isinstance(n,bool) or not isinstance(n,int) or not 2<=n<=1000 for n in (train_samples,validation_samples,test_samples)):
        raise ValueError('Require 2–1000 samples per split')
    p=Problem.parse(raw)
    # Separate deterministic streams; no historical 200-trial data is used here.
    sampled(p,seed,2) # validate seed
    streams=np.random.SeedSequence(seed).spawn(4)
    split_seeds={k:int(s.generate_state(1)[0]) for k,s in zip(('training','validation','heldout','mutation'),streams)}
    training=[Scenario('train:'+s.id,s.availability,s.supply_factor,s.demand_factor) for s in sampled(p,split_seeds['training'],train_samples)]
    declared_ss=declared(p)
    rng=np.random.default_rng(split_seeds['mutation'])
    archive=[];history=[]
    def emit(stage,**data):
        if progress:progress(dict(stage=stage,**data))
    def evaluate(capacity,parents,generation,mutation):
        cid=f'g{generation}-c{len(archive):03d}'
        cost=float(sum(e.unit_cost*c for e,c in zip(p.edges,capacity)))
        ds=[simulate(p,capacity,s) for s in declared_ss]
        ts=[simulate(p,capacity,s) for s in training]
        for ss,rs in ((declared_ss,ds),(training,ts)):
            for scenario,result in zip(ss,rs):result['independent_audit']=audit_result(p,capacity,scenario,result)
        c=dict(id=cid,parents=parents,generation=generation,mutations=mutation,capacities=list(capacity),cost=cost,
               declared=dict(results=ds),training=dict(results=ts,metrics=metrics(p,ts)),verification=verify(p,capacity,ds),
               failure_history=[r['scenario_id'] for r in ds+ts if not r['passes']],
               disposition='pending',rejection_reason=None)
        archive.append(c);emit('candidate_evaluated',candidate_id=cid,generation=generation,cost=cost)
        return c
    nominal=synthesise(p,declared_ss[:1]);robust=synthesise(p,declared_ss)
    if nominal['capacities'] is not None:evaluate(nominal['capacities'],[],0,[dict(operator='nominal_lp')])
    if robust['capacities'] is not None:evaluate(robust['capacities'],[],0,[dict(operator='declared_scenario_lp')])
    uniform=[min(e.max_capacity,p.budget/sum(e.unit_cost for e in p.edges)) for e in p.edges]
    evaluate(uniform,[],0,[dict(operator='uniform_budget_allocation')])
    # Counterexample-informed cross-scenario design: no held-out access.
    cross=[Scenario('cross:'+s.id,s.availability,.95,1.25) for s in declared_ss if s.id.startswith(('pipe-loss:','corridor-loss:'))]+declared_ss
    cross_design=synthesise(p,cross)
    if cross_design['capacities'] is not None:evaluate(cross_design['capacities'],[],0,[dict(operator='outage_demand_cross_lp',demand_factor=1.25,supply_factor=.95)])
    infeasible_attempts=[] if cross_design['capacities'] is not None else [dict(operator='outage_demand_cross_lp',status='infeasible',solver_message=cross_design['message'])]
    previous=None;stagnation=0;stop='generation_budget'
    for generation in range(1,generations+1):
        frontier=pareto_front(archive)
        if not frontier:stop='no_declared_feasible_parent';break
        parents=sorted((c for c in archive if c['id'] in frontier),key=lambda c:(c['training']['metrics']['failure_rate'],c['cost'],c['id']))[:4]
        history.append(dict(generation=generation-1,frontier=frontier,parent_ids=[c['id'] for c in parents]))
        for parent in parents:
            # Two meaningful operators: bottleneck-aware capacity increase and
            # cost/redundancy tradeoff through a seeded capacity perturbation.
            train=parent['training']['results']
            worst=min(train,key=lambda r:r['service_fraction'])
            worst_s=next(s for s in training if s.id==worst['scenario_id'])
            saturated=[i for i,(f,c,a) in enumerate(zip(worst['flow'],parent['capacities'],worst_s.availability)) if a>0 and abs(f-c*a)<1e-6]
            targets=saturated or list(range(len(p.edges)))
            for operator in ('bottleneck_reinforcement','capacity_tradeoff'):
                c=np.array(parent['capacities'])
                if operator=='bottleneck_reinforcement':
                    selected=targets;factor=float(rng.uniform(1.08,1.3));c[selected]*=factor
                else:
                    selected=[int(rng.integers(len(c)))];factor=float(rng.uniform(.75,1.25));c[selected]*=factor
                c=np.minimum(c,[e.max_capacity for e in p.edges])
                cost=np.dot(c,[e.unit_cost for e in p.edges])
                if cost>p.budget:c*=p.budget/cost
                evaluate(c.tolist(),[parent['id']],generation,[dict(operator=operator,edges=[p.edges[i].id for i in selected],factor=factor,training_counterexample=worst['scenario_id'],budget_projection=bool(cost>p.budget))])
        current=pareto_front(archive)
        # Deterministic fixed-budget stopping; stagnation observed but does not
        # falsely imply convergence of a stochastic population.
        signature=tuple((round(c['cost'],6),c['training']['metrics']['failures'],round(c['training']['metrics']['mean_unmet_m3h'],6)) for c in archive if c['id'] in current)
        stagnation=stagnation+1 if signature==previous else 0;previous=signature
        emit('generation_complete',generation=generation,frontier=current)
    frontier=pareto_front(archive)
    for c in archive:
        if not c['verification']['requirements_pass']:
            c.update(disposition='rejected',rejection_reason='Declared service or budget constraint failed')
        elif c['id'] not in frontier:
            c.update(disposition='dominated',rejection_reason='Training Pareto dominated; all evidence retained')
        else:c['disposition']='pareto_survivor'
    recommendation=min((c for c in archive if c['id'] in frontier),key=lambda c:(c['training']['metrics']['failure_rate'],c['training']['metrics']['mean_unmet_m3h'],c['cost'],c['id']))['id'] if frontier else None
    emit('selection_frozen',recommendation=recommendation)
    # Construct these only after the training-selected recommendation is frozen.
    validation=[Scenario('validation:'+s.id,s.availability,s.supply_factor,s.demand_factor) for s in sampled(p,split_seeds['validation'],validation_samples)]
    heldout=[Scenario('test:'+s.id,s.availability,s.supply_factor,s.demand_factor) for s in sampled(p,split_seeds['heldout'],test_samples)]
    for c in archive:
        for split,ss in [('validation',validation),('heldout',heldout)]:
            rs=[simulate(p,c['capacities'],s) for s in ss]
            for scenario,result in zip(ss,rs):result['independent_audit']=audit_result(p,c['capacities'],scenario,result)
            c[split]=dict(results=rs,metrics=metrics(p,rs))
        c['visual_fields'] = []
        for i,e in enumerate(p.edges):
            indices=[j for j,scenario in enumerate(heldout) if scenario.availability[i]==0]
            failures=sum(not c['heldout']['results'][j]['passes'] for j in indices)
            c['visual_fields'].append(dict(edge_id=e.id,outage_trials=len(indices),outage_failures=failures,conditional_failure_rate=failures/len(indices) if indices else None,conditional_wilson_95=wilson(failures,len(indices)) if indices else None,scope='Held-out failure conditional on this edge outage; other disturbances can co-occur'))
        c['failure_history'].extend(r['scenario_id'] for split in ('validation','heldout') for r in c[split]['results'] if not r['passes'])
        emit('audit_complete',candidate_id=c['id'])
    chosen=next((c for c in archive if c['id']==recommendation),None)
    attack=discover(p,chosen['capacities']) if chosen else None
    diagnosis=diagnose(p,chosen['capacities'],heldout,chosen['heldout']['results']) if chosen else None
    sensitivity_seed=int(np.random.SeedSequence([seed,314159]).generate_state(1)[0])
    sensitivity_result=sensitivity(p,chosen['capacities'],sampled(p,sensitivity_seed,min(train_samples,60))) if chosen else None
    ss=dict(declared=declared_ss,training=training,validation=validation,heldout=heldout)
    science=dict(schema_version='2.0',model_version=EVOLUTION_VERSION,configuration=raw,
                 experiment_config=dict(seed=seed,generations=generations,train_samples=train_samples,validation_samples=validation_samples,test_samples=test_samples),
                 seeds=split_seeds,distribution=DISTRIBUTION,scenarios={k:[asdict(s) for s in v] for k,v in ss.items()},
                 candidates=archive,pareto_frontier=frontier,recommendation=recommendation,
                 selection_policy='Declared feasible; lexicographic training failure rate, unmet demand, cost. Frozen before validation/test.',
                 stopping=dict(reason=stop,stagnant_generations=stagnation),optimisation_history=history,
                 infeasible_attempts=infeasible_attempts,adversarial=attack,failure_taxonomy=diagnosis,
                 sensitivity=dict(seed=sensitivity_seed,analysis=sensitivity_result),
                 provenance=provenance_graph(p,archive,ss,recommendation),
                 software=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,solver='HiGHS'),
                 limitations=['Numerical steady-state capacity model, not hydraulics','Synthetic hazards, not field probabilities','Training frontier is empirical, not a global Pareto guarantee','Adversarial search bounded and non-IID','No temporal cascade or recovery','No mathematical or formal verification'])
    digest=hashlib.sha256(canonical(science).encode()).hexdigest()
    return dict(experiment_id='deva-evolution-'+digest[:16],scientific_sha256=digest,timestamp=datetime.now(timezone.utc).isoformat(),science=science)
