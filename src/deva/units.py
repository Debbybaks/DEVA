"""Small dimension-checked quantity boundary; all hydraulic kernels use SI."""

from dataclasses import dataclass
import math

# dimensions: length, time, mass; synthetic cost remains explicitly dimensionless.
UNITS = {
    "m": (1.0, (1, 0, 0)),
    "mm": (0.001, (1, 0, 0)),
    "s": (1.0, (0, 1, 0)),
    "h": (3600.0, (0, 1, 0)),
    "m3": (1.0, (3, 0, 0)),
    "L": (0.001, (3, 0, 0)),
    "m3/s": (1.0, (3, -1, 0)),
    "m3/h": (1 / 3600.0, (3, -1, 0)),
    "L/s": (0.001, (3, -1, 0)),
    "m/s": (1.0, (1, -1, 0)),
    "m/s2": (1.0, (1, -2, 0)),
    "kg/m3": (1.0, (-3, 0, 1)),
    "m2": (1.0, (2, 0, 0)),
    "Pa": (1.0, (-1, -2, 1)),
    "W": (1.0, (2, -3, 1)),
    "kW": (1000.0, (2, -3, 1)),
    "J": (1.0, (2, -2, 1)),
    "Wh": (3600.0, (2, -2, 1)),
    "kWh": (3600000.0, (2, -2, 1)),
    "1": (1.0, (0, 0, 0)),
}


@dataclass(frozen=True)
class Quantity:
    si: float
    dimension: tuple[int, int, int]

    @classmethod
    def of(cls, value, unit):
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or unit not in UNITS
        ):
            raise ValueError("Finite quantity and known unit required")
        scale, dim = UNITS[unit]
        return cls(float(value) * scale, dim)

    def to(self, unit):
        scale, dim = UNITS[unit]
        if dim != self.dimension:
            raise ValueError("Incompatible dimensions")
        return self.si / scale

    def __add__(self, other):
        if self.dimension != other.dimension:
            raise ValueError("Incompatible dimensions")
        return Quantity(self.si + other.si, self.dimension)

    def __mul__(self, other):
        return Quantity(
            self.si * other.si,
            tuple(a + b for a, b in zip(self.dimension, other.dimension)),
        )

    def __truediv__(self, other):
        return Quantity(
            self.si / other.si,
            tuple(a - b for a, b in zip(self.dimension, other.dimension)),
        )


def si(raw, unit, positive=False):
    if not isinstance(raw, dict) or set(raw) != {"value", "unit"}:
        raise ValueError("Quantity requires value and unit")
    value = Quantity.of(raw["value"], raw["unit"]).to(unit)
    if positive and value <= 0:
        raise ValueError("Positive physical quantity required")
    return value
