"""Tests for energy unit enum and measurement conversion."""

import pytest

from leo.models.electrical import Energy, EnergyUnit, Power, PowerUnit


class TestEnergyUnit:
    def test_kwh_is_1000_wh(self) -> None:
        assert EnergyUnit.KWH.multiplier == 1_000 * EnergyUnit.WH.multiplier

    def test_mwh_is_1000000_wh(self) -> None:
        assert EnergyUnit.MWH.multiplier == 1_000_000 * EnergyUnit.WH.multiplier

    def test_labels(self) -> None:
        assert str(EnergyUnit.WH) == "Wh"
        assert str(EnergyUnit.KWH) == "kWh"
        assert str(EnergyUnit.MWH) == "MWh"


class TestMeasurementTo:
    def test_kwh_to_j(self) -> None:
        energy = Energy(value=1.0, unit=EnergyUnit.KWH)
        result = energy.to(EnergyUnit.J)
        assert result.value == pytest.approx(3_600_000.0)
        assert result.unit == EnergyUnit.J

    def test_j_to_kwh(self) -> None:
        energy = Energy(value=3_600_000.0, unit=EnergyUnit.J)
        result = energy.to(EnergyUnit.KWH)
        assert result.value == pytest.approx(1.0)
        assert result.unit == EnergyUnit.KWH

    def test_same_unit(self) -> None:
        energy = Energy(value=42.0, unit=EnergyUnit.WH)
        result = energy.to(EnergyUnit.WH)
        assert result.value == pytest.approx(42.0)

    def test_incompatible_units_raises(self) -> None:
        energy = Energy(value=1.0, unit=EnergyUnit.KWH)
        with pytest.raises(TypeError, match="Cannot convert"):
            energy.to(PowerUnit.W)

    def test_power_to(self) -> None:
        power = Power(value=1.0, unit=PowerUnit.KW)
        result = power.to(PowerUnit.W)
        assert result.value == pytest.approx(1000.0)
        assert result.unit == PowerUnit.W
