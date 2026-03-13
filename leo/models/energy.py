from enum import Enum


class EnergyUnit(Enum):
    """Unit of energy with label and watt-hour multiplier."""

    WH = ("Wh", 1)
    KWH = ("kWh", 1_000)
    MWH = ("MWh", 1_000_000)

    def __init__(self, label: str, multiplier: int) -> None:
        self.label = label
        self.multiplier = multiplier

    def __str__(self) -> str:
        return self.label
