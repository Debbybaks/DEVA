"""Explicit trusted plugins; never import user-supplied code."""

from .domains.water import WaterDomain
from .domains.microgrid import MicrogridDomain
from .domain_contract import validate_domain


def construct(identity, raw):
    registry = {"water": WaterDomain, "microgrid": MicrogridDomain}
    if identity not in registry:
        raise ValueError("Unknown registered domain")
    return validate_domain(registry[identity](raw))
