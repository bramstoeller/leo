from __future__ import annotations

from enum import Enum
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound="Measurement")


class Unit(Enum):
    def __init__(self, label: str, multiplier: float) -> None:
        self.label = label
        self.multiplier = multiplier

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return self.label


class PowerUnit(Unit):
    W = ("W", 1)
    KW = ("kW", 1_000)
    MW = ("MW", 1_000_000)


class EnergyUnit(Unit):
    J = ("J", 1)
    WS = ("Ws", 1)
    WH = ("Wh", 3_600)
    KWH = ("kWh", 3_600_000)
    MWH = ("MWh", 3_600_000_000)


class Measurement(BaseModel):
    value: float
    unit: Unit

    def si(self) -> float:
        return self.value * self.unit.multiplier

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return f"{self.value} {self.unit}"

    def to(self: T, unit: Unit) -> T:
        """Convert this measurement to a different unit of the same kind."""
        if type(self.unit) is not type(unit):
            raise TypeError(f"Cannot convert {type(self.unit).__name__} to {type(unit).__name__}")
        return type(self)(value=self.si() / unit.multiplier, unit=unit)

    def __neg__(self: T) -> T:
        return type(self)(value=-self.value, unit=self.unit)

    def __add__(self: T, other: T) -> T:
        if type(self) is not type(other):
            raise TypeError(f"Cannot add {type(other).__name__} to {type(self).__name__}!")
        total = self.si() + other.si()
        unit = self.unit if self.unit.multiplier >= other.unit.multiplier else other.unit
        return type(self)(value=total / unit.multiplier, unit=unit)

    def __sub__(self: T, other: T) -> T:
        if type(self) is not type(other):
            raise TypeError(f"Cannot subtract {type(other).__name__} from {type(self).__name__}!")
        return self + (-other)


class Power(Measurement):
    unit: PowerUnit


class Energy(Measurement):
    unit: EnergyUnit
