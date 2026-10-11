"""Declared threats and a separate, reproducible synthetic IID distribution."""
import numpy as np
from .model import Scenario


def declared(p):
    m = len(p.edges)
    output = [Scenario('nominal', (1.,)*m)]
    for i, edge in enumerate(p.edges):
        a = [1.]*m; a[i] = 0.
        output.append(Scenario(f'pipe-loss:{edge.id}', tuple(a)))
    for corridor in sorted({e.corridor for e in p.edges}):
        output.append(Scenario(f'corridor-loss:{corridor}', tuple(float(e.corridor != corridor) for e in p.edges)))
    output.extend([Scenario('demand-surge', (1.,)*m, demand_factor=1.2),
                   Scenario('supply-shortage', (1.,)*m, supply_factor=.8)])
    return output


def sampled(p, seed, count):
    if isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= 10000:
        raise ValueError('Require 1–10000 samples')
    if isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed < 2**32:
        raise ValueError('Seed must be uint32')
    rng = np.random.default_rng(seed)
    corridors = sorted({e.corridor for e in p.edges})
    output = []
    for i in range(count):
        a = (rng.random(len(p.edges)) >= .03).astype(float)
        if rng.random() < .08:
            corridor = corridors[int(rng.integers(len(corridors)))]
            a *= [e.corridor != corridor for e in p.edges]
        output.append(Scenario(f'heldout:{i:05d}', tuple(a), float(rng.uniform(.75, 1)), float(rng.uniform(.9, 1.35))))
    return output


DISTRIBUTION = dict(individual_pipe_loss_probability=.03, corridor_loss_probability=.08,
                    supply_uniform=[.75, 1.], demand_uniform=[.9, 1.35],
                    caveat='Synthetic IID scenario distribution; not calibrated real-world failure probabilities.')
