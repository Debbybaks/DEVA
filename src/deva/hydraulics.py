"""Independent steady-state passive Darcy–Weisbach research model.

This model requires explicit geometry; capacity designs do not imply diameters.
Constant demands can produce negative pressure; report infeasibility of pressure
requirements rather than silently reducing demand. No calibrated field accuracy.
"""
from dataclasses import dataclass
import math
import numpy as np
from scipy.optimize import least_squares

G=9.80665
HYDRAULIC_VERSION='passive-darcy-weisbach-0.1'


@dataclass(frozen=True)
class Pipe:
    id: str
    tail: str
    head: str
    length_m: float
    diameter_m: float
    friction_factor: float

    @property
    def resistance(self):
        values=(self.length_m,self.diameter_m,self.friction_factor)
        if not all(math.isfinite(v) and v>0 for v in values):
            raise ValueError('Positive finite pipe geometry and Darcy factor required')
        return 8*self.friction_factor*self.length_m/(G*math.pi**2*self.diameter_m**5)


def solve_hydraulics(nodes, pipes, fixed_heads_m, demands_m3s, elevations_m, minimum_pressure_m=10.):
    nodes=tuple(nodes); pipes=tuple(pipes)
    if len(set(nodes))!=len(nodes) or not 2<=len(nodes)<=100 or not 1<=len(pipes)<=300:
        raise ValueError('Invalid hydraulic graph')
    if not fixed_heads_m or set(fixed_heads_m)-set(nodes) or set(demands_m3s)-set(nodes) or set(elevations_m)!=set(nodes):
        raise ValueError('Invalid hydraulic node maps')
    if set(fixed_heads_m)&set(demands_m3s):
        raise ValueError('Fixed-head boundaries cannot also have specified demands')
    if len({p.id for p in pipes})!=len(pipes) or any(p.tail not in nodes or p.head not in nodes or p.tail==p.head for p in pipes):
        raise ValueError('Invalid hydraulic pipes')
    if not math.isfinite(minimum_pressure_m) or minimum_pressure_m<0:
        raise ValueError('Invalid minimum pressure')
    vals=[*fixed_heads_m.values(),*demands_m3s.values(),*elevations_m.values()]
    if not all(math.isfinite(v) for v in vals) or any(v<0 for v in demands_m3s.values()):
        raise ValueError('Invalid hydraulic parameters')
    # Every component requires a fixed-head anchor to avoid an undetermined head.
    visited=set(fixed_heads_m)
    while True:
        grown=visited|{p.head for p in pipes if p.tail in visited}|{p.tail for p in pipes if p.head in visited}
        if grown==visited:break
        visited=grown
    if visited!=set(nodes):
        raise ValueError('Hydraulic component lacks fixed-head boundary')
    free=[n for n in nodes if n not in fixed_heads_m]
    m=len(pipes);b=np.zeros((len(free),m))
    for j,p in enumerate(pipes):
        if p.tail in free:b[free.index(p.tail),j]=-1
        if p.head in free:b[free.index(p.head),j]=1
    d=np.array([demands_m3s.get(n,0.) for n in free])
    r=np.array([p.resistance for p in pipes])
    flow_scale=max(float(d.sum()),.001)
    head_scale=max(max(abs(v) for v in fixed_heads_m.values()),1.)
    def state(x):
        heads={**fixed_heads_m,**dict(zip(free,x[m:]*head_scale))}
        q=x[:m]*flow_scale
        return heads,q
    def residual(x):
        heads,q=state(x)
        loss=np.array([heads[p.tail]-heads[p.head] for p in pipes])-r*q*np.abs(q)
        return np.concatenate(((b@q-d)/flow_scale,loss/head_scale))
    initial=np.concatenate((np.full(m,1/max(m,1)),np.full(len(free),np.mean(list(fixed_heads_m.values()))/head_scale)))
    result=least_squares(residual,initial,xtol=1e-12,ftol=1e-12,gtol=1e-12,max_nfev=5000)
    heads,q=state(result.x)
    mass=float(np.max(np.abs(b@q-d))) if free else 0.
    energy=float(np.max(np.abs(np.array([heads[p.tail]-heads[p.head] for p in pipes])-r*q*np.abs(q))))
    if not result.success or mass>1e-8 or energy>1e-6:
        raise RuntimeError(f'Hydraulic nonlinear solve failed validation: mass={mass}, energy={energy}')
    pressure={n:float(heads[n]-elevations_m[n]) for n in nodes}
    injections={n:float(sum(q[j] for j,p in enumerate(pipes) if p.tail==n)-sum(q[j] for j,p in enumerate(pipes) if p.head==n)) for n in fixed_heads_m}
    return dict(model_version=HYDRAULIC_VERSION,head_m={n:float(heads[n]) for n in nodes},pressure_head_m=pressure,
                flow_m3s=q.tolist(),boundary_injection_m3s=injections,mass_residual_m3s=mass,energy_residual_m=energy,
                minimum_pressure_m=minimum_pressure_m,pressure_requirement_pass=all(pressure[n]>=minimum_pressure_m for n in free),
                verification='SIMULATED',solver='scipy.optimize.least_squares',
                scope='Uncalibrated steady-state passive pipes; fixed friction; prescribed demand, fixed-head reservoirs; no pumps, storage, transients or source capacity constraints')
