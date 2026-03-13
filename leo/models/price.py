from enum import StrEnum

from pydantic import AwareDatetime, BaseModel

from leo.models.energy import EnergyUnit


class Currency(StrEnum):
    """Currency code with symbol as value."""

    EUR = "€"
    USD = "$"
    GBP = "£"


class EnergyPrice(BaseModel):
    """Price for a specific time range and energy unit."""

    amount: float
    currency: Currency
    energy_unit: EnergyUnit

    def __str__(self) -> str:
        return f"{self.amount:.4f} {self.currency}/{self.energy_unit}"


class EnergyPriceSlot(BaseModel):
    """Electricity price for 1kWh for a specific time range."""

    timestamp_from: AwareDatetime
    timestamp_till: AwareDatetime
    price: EnergyPrice

    def __str__(self) -> str:
        dt_from = self.timestamp_from.astimezone()
        dt_till = self.timestamp_till.astimezone()
        return f"{dt_from.date()} {dt_from.time()}-{dt_till.time()}: {self.price}"
