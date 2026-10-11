"""Minimal general engineering contract; domain plugins retain physical authority."""

from typing import Protocol
import math
from .units import UNITS


class EngineeringDomain(Protocol):
    descriptor: dict
    configuration: dict
    variables: list[dict]
    baseline: list[float]

    def cost(self, design: list[float]) -> float: ...
    def simulate(self, design: list[float], scenario: dict) -> dict: ...
    def scenarios(self, seed: int, count: int, severity: float = 1.0) -> list[dict]: ...
    def mutations(
        self, design: list[float], counterexample: dict | None
    ) -> list[list[float]]: ...
    def verify(self, design: list[float]) -> list[dict]: ...


def validate_domain(domain):
    required = {
        "id",
        "model_version",
        "component_types",
        "state_variables",
        "equations",
        "constraints",
        "failure_mechanisms",
        "uncertainty",
        "observables",
        "verifiable_properties",
        "visualisation",
        "evidence",
        "validity_envelope",
    }
    if set(domain.descriptor) != required:
        raise ValueError("Exact domain descriptor required")
    if not domain.descriptor["id"] or not domain.descriptor["model_version"]:
        raise ValueError("Domain identity/version required")
    for variable in domain.descriptor["state_variables"]:
        if variable["unit"] not in UNITS:
            raise ValueError("Unknown state unit")
    if not domain.variables or len(domain.baseline) != len(domain.variables):
        raise ValueError("Explicit design variables and baseline required")
    if len({v["id"] for v in domain.variables}) != len(domain.variables):
        raise ValueError("Distinct optimisation variable IDs required")
    for spec, value in zip(domain.variables, domain.baseline):
        if (
            spec["unit"] not in UNITS
            or not spec["options"]
            or value not in spec["options"]
        ):
            raise ValueError("Bounded baseline in declared units/catalogue required")
        if any(
            isinstance(x, bool)
            or not isinstance(x, (int, float))
            or not math.isfinite(x)
            or x < 0
            for x in spec["options"]
        ):
            raise ValueError("Finite nonnegative catalogue required")
    return domain


def validate_outcome(domain, outcome):
    if (
        outcome["domain"] != domain.descriptor["id"]
        or outcome["model_version"] != domain.descriptor["model_version"]
    ):
        raise ValueError("Cross-domain/model evidence rejected")
    service = outcome["service"]
    if service is not None and (
        not math.isfinite(service) or not 0 <= service <= 1 + 1e-7
    ):
        raise ValueError("Invalid service quantity")
    if outcome["passes"] and (service is None or outcome["violations"]):
        raise ValueError("Unsupported requirement pass")
    return outcome
