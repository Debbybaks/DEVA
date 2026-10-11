"""Independent evidence checking without trusting solver-reported pass/residual."""
import hashlib
import numpy as np
from .model import TOL, incidence
from .experiment import canonical


def audit_result(p,capacities,scenario,result):
    scenario.validate(p)
    m,n=len(p.edges),len(p.nodes)
    arrays={name:np.asarray(result[name],dtype=float) for name in ('flow','injection','delivered','demand')}
    for name,a in arrays.items():
        if a.shape!=(m if name=='flow' else n,) or not np.isfinite(a).all():
            raise ValueError(f'Invalid evidence vector {name}')
    c=np.asarray(capacities,dtype=float)
    if c.shape!=(m,) or not np.isfinite(c).all():raise ValueError('Invalid capacities')
    f,q,y,d=(arrays[k] for k in ('flow','injection','delivered','demand'))
    expected_d=np.asarray(p.demand)*scenario.demand_factor
    expected_s=np.asarray(p.supply)*scenario.supply_factor
    residual=max(float(np.max(np.abs(incidence(p)@f+q-y))),float(np.max(np.abs(d-expected_d))),
                 float(np.max(-f)),float(np.max(-q)),float(np.max(-y)),
                 float(np.max(f-c*scenario.availability)),float(np.max(q-expected_s)),float(np.max(y-d)),0.)
    t=float(result['service_fraction'])
    service=min(float(yv/dv) for yv,dv in zip(y,d) if dv>0)
    residual=max(residual,abs(t-service),max(0.,-t,t-1))
    if not np.isfinite(t) or residual>TOL:
        raise ValueError(f'Evidence invalid: independent residual={residual}')
    if result['scenario_id']!=scenario.id:raise ValueError('Scenario identity mismatch')
    passed=bool(service>=p.target-TOL)
    if result['passes']!=passed:raise ValueError('Evidence pass flag contradicts delivered service')
    return dict(independent_max_residual=residual,minimum_delivered_fraction=service,passes=passed,
                scope='Numerical primal feasibility check; no optimality certificate or formal proof')


def verify_hash(envelope):
    digest=hashlib.sha256(canonical(envelope['science']).encode()).hexdigest()
    if digest!=envelope['scientific_sha256']:raise ValueError('Scientific payload checksum mismatch')
    return digest


def ancestors(graph,node_id):
    ids={n['id'] for n in graph['nodes']}
    if node_id not in ids:raise ValueError('Unknown provenance node')
    seen={node_id}
    while True:
        more=seen|{e['source'] for e in graph['edges'] if e['target'] in seen}
        if more==seen:return sorted(seen)
        seen=more
