"""Tests for energy unit enum."""

from leo.models.energy import EnergyUnit


class TestEnergyUnit:
    def test_kwh_is_1000_wh(self) -> None:
        assert EnergyUnit.KWH.multiplier == 1_000 * EnergyUnit.WH.multiplier

    def test_mwh_is_1000000_wh(self) -> None:
        assert EnergyUnit.MWH.multiplier == 1_000_000 * EnergyUnit.WH.multiplier

    def test_labels(self) -> None:
        assert str(EnergyUnit.WH) == "Wh"
        assert str(EnergyUnit.KWH) == "kWh"
        assert str(EnergyUnit.MWH) == "MWh"
