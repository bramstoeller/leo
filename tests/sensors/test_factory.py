"""Tests for sensor factory functions."""

import pytest

from leo.sensors import get_power_meter
from leo.sensors.homewizard import get_hw_power_meter
from leo.sensors.homewizard.power_meter import HomeWizardPowerMeter1Phase, HomeWizardPowerMeter3Phase


class TestGetHwPowerMeter:
    def test_p1_returns_3phase(self) -> None:
        meter = get_hw_power_meter(meter_type="p1", host="192.168.1.1")
        assert isinstance(meter, HomeWizardPowerMeter3Phase)

    def test_kwh_3phase_returns_3phase(self) -> None:
        meter = get_hw_power_meter(meter_type="kwh_3phase", host="192.168.1.1")
        assert isinstance(meter, HomeWizardPowerMeter3Phase)

    def test_kwh_1phase_returns_1phase(self) -> None:
        meter = get_hw_power_meter(meter_type="kwh_1phase", host="192.168.1.1", phase=1)
        assert isinstance(meter, HomeWizardPowerMeter1Phase)

    def test_power_socket_returns_1phase(self) -> None:
        meter = get_hw_power_meter(meter_type="power_socket", host="192.168.1.1", phase=2)
        assert isinstance(meter, HomeWizardPowerMeter1Phase)

    def test_1phase_missing_phase_raises(self) -> None:
        with pytest.raises(ValueError, match="Phase must be specified"):
            get_hw_power_meter(meter_type="kwh_1phase", host="192.168.1.1")

    def test_1phase_invalid_phase_raises(self) -> None:
        with pytest.raises(ValueError, match="Phase must be 1, 2, or 3"):
            get_hw_power_meter(meter_type="kwh_1phase", host="192.168.1.1", phase=5)


class TestGetPowerMeter:
    def test_homewizard_routes_correctly(self) -> None:
        meter = get_power_meter(brand="homewizard", meter_type="p1", host="192.168.1.1")
        assert isinstance(meter, HomeWizardPowerMeter3Phase)
