from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


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


class Power(Measurement):
    unit: PowerUnit


class Energy(Measurement):
    unit: EnergyUnit
