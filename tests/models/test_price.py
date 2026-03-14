"""Tests for price models."""

from datetime import UTC, datetime

import pytest

from leo.models.electrical import EnergyUnit
from leo.models.price import Currency, EnergyPrice, EnergyPriceSlot


class TestEnergyPrice:
    def test_str(self) -> None:
        price = EnergyPrice(amount=0.1234, currency=Currency.EUR, energy_unit=EnergyUnit.KWH)
        assert str(price) == "0.1234 €/kWh"

    def test_str_different_unit(self) -> None:
        price = EnergyPrice(amount=123.4, currency=Currency.USD, energy_unit=EnergyUnit.MWH)
        assert str(price) == "123.4000 $/MWh"


class TestEnergyPriceSlot:
    def test_str_contains_price(self) -> None:
        slot = EnergyPriceSlot(
            timestamp_from=datetime(2026, 3, 13, 10, 0, tzinfo=UTC),
            timestamp_till=datetime(2026, 3, 13, 10, 15, tzinfo=UTC),
            price=EnergyPrice(amount=0.15, currency=Currency.EUR, energy_unit=EnergyUnit.KWH),
        )
        result = str(slot)
        assert "0.1500" in result
        assert "€/kWh" in result

    def test_rejects_naive_timestamps(self) -> None:
        with pytest.raises(ValueError):
            EnergyPriceSlot(
                timestamp_from=datetime(2026, 3, 13, 10, 0),
                timestamp_till=datetime(2026, 3, 13, 10, 15),
                price=EnergyPrice(amount=0.15, currency=Currency.EUR, energy_unit=EnergyUnit.KWH),
            )
