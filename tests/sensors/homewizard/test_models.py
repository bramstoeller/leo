"""Tests for HomeWizard PowerMeterData model."""

from leo.models.electrical import Energy, EnergyUnit, Power, PowerUnit
from leo.sensors.homewizard.models import PowerMeterData


class TestTotalImport:
    def test_returns_energy(self) -> None:
        data = PowerMeterData(total_power_import_kwh=123.45)
        result = data.total_import
        assert result == Energy(value=123.45, unit=EnergyUnit.KWH)

    def test_none_when_missing(self) -> None:
        assert PowerMeterData().total_import is None


class TestTotalExport:
    def test_returns_energy(self) -> None:
        data = PowerMeterData(total_power_export_kwh=67.89)
        result = data.total_export
        assert result == Energy(value=67.89, unit=EnergyUnit.KWH)

    def test_none_when_missing(self) -> None:
        assert PowerMeterData().total_export is None


class TestActivePower:
    def test_l1(self) -> None:
        data = PowerMeterData(active_power_l1_w=100.0)
        assert data.active_power_l1 == Power(value=100.0, unit=PowerUnit.W)

    def test_l2(self) -> None:
        data = PowerMeterData(active_power_l2_w=200.0)
        assert data.active_power_l2 == Power(value=200.0, unit=PowerUnit.W)

    def test_l3(self) -> None:
        data = PowerMeterData(active_power_l3_w=300.0)
        assert data.active_power_l3 == Power(value=300.0, unit=PowerUnit.W)

    def test_none_when_missing(self) -> None:
        data = PowerMeterData()
        assert data.active_power_l1 is None
        assert data.active_power_l2 is None
        assert data.active_power_l3 is None
