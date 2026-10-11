"""Bounded, strict structured interpretation. No arbitrary code execution."""
from dataclasses import dataclass
import math


def number(value, name, maximum=1e9):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be numeric")
    if not math.isfinite(value) or not 0 <= value <= maximum:
        raise ValueError(f"{name} must be finite in [0, {maximum}]")
    return float(value)


def keys(obj, expected):
    if not isinstance(obj, dict) or set(obj) != set(expected):
        raise ValueError(f"Expected exactly {sorted(expected)}")


@dataclass(frozen=True)
class Edge:
    id: str
    tail: str
    head: str
    unit_cost: float
    max_capacity: float
    corridor: str


@dataclass(frozen=True)
class Problem:
    id: str
    objective: str
    nodes: tuple[str, ...]
    edges: tuple[Edge, ...]
    supply: tuple[float, ...]
    demand: tuple[float, ...]
    budget: float
    target: float

    @classmethod
    def parse(cls, raw):
        keys(raw, ['id', 'objective', 'nodes', 'edges', 'supply', 'demand', 'budget', 'target'])
        for name in ('id', 'objective'):
            if not isinstance(raw[name], str) or not 1 <= len(raw[name]) <= 4000:
                raise ValueError(f"Invalid {name}")
        nodes = raw['nodes']
        if not isinstance(nodes, list) or not 2 <= len(nodes) <= 100:
            raise ValueError('Require 2–100 nodes')
        if any(not isinstance(n, str) or not 1 <= len(n) <= 100 for n in nodes) or len(set(nodes)) != len(nodes):
            raise ValueError('Node names must be unique nonempty strings')
        if not isinstance(raw['edges'], list) or not 1 <= len(raw['edges']) <= 300:
            raise ValueError('Require 1–300 edges')
        edges = []
        for e in raw['edges']:
            keys(e, ['id', 'tail', 'head', 'unit_cost', 'max_capacity', 'corridor'])
            if any(not isinstance(e[k], str) or not 1 <= len(e[k]) <= 100 for k in ('id', 'corridor')):
                raise ValueError('Invalid edge identifier/corridor')
            if e['tail'] not in nodes or e['head'] not in nodes or e['tail'] == e['head']:
                raise ValueError('Invalid edge endpoints')
            cost = number(e['unit_cost'], 'unit_cost')
            if cost == 0:
                raise ValueError('Unit cost must be positive')
            edges.append(Edge(e['id'], e['tail'], e['head'], cost, number(e['max_capacity'], 'max_capacity'), e['corridor']))
        if len({e.id for e in edges}) != len(edges):
            raise ValueError('Duplicate edge IDs')
        arrays = []
        for field in ('supply', 'demand'):
            values = raw[field]
            if not isinstance(values, dict) or set(values) - set(nodes):
                raise ValueError(f'Invalid {field} node map')
            arrays.append(tuple(number(values.get(n, 0), field) for n in nodes))
        if sum(arrays[0]) == 0 or sum(arrays[1]) == 0:
            raise ValueError('Positive total supply and demand required')
        return cls(raw['id'], raw['objective'], tuple(nodes), tuple(edges), *arrays,
                   number(raw['budget'], 'budget'), number(raw['target'], 'target', 1))
