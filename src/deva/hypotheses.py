"""Explicit domain-scoped hypothesis lifecycle, not generated reasoning."""

from copy import deepcopy

TRANSITIONS = {
    "PROPOSED": {"TESTING"},
    "TESTING": {"SUPPORTED", "WEAKENED", "REJECTED", "INCONCLUSIVE"},
    "SUPPORTED": {"TESTING"},
    "WEAKENED": {"TESTING"},
    "REJECTED": {"TESTING"},
    "INCONCLUSIVE": {"TESTING"},
}


def update(hypothesis, status, evidence):
    if status not in TRANSITIONS.get(hypothesis["status"], set()):
        raise ValueError("Invalid hypothesis transition")
    if status != "TESTING" and not evidence:
        raise ValueError("A conclusion requires explicit experimental evidence")
    if any(
        e["domain"] != hypothesis["domain"] or not e["reference"] or not e["scope"]
        for e in evidence
    ):
        raise ValueError("Domain-correct references and claim scope required")
    result = deepcopy(hypothesis)
    result["status"] = status
    result.setdefault("history", []).append(
        dict(previous=hypothesis["status"], status=status, evidence=evidence)
    )
    return result
