"""Tests for system_check sensor verification."""

from typing import Any
from unittest.mock import MagicMock, patch

from leo.__main__ import system_check
from leo.config import Config, SensorConfig
from leo.exceptions import FetchError
from leo.meters.homewizard import HomeWizardMeterType


def _sensor(host: str, meter_type: HomeWizardMeterType, phase: int | None = None) -> SensorConfig:
    return SensorConfig(host=host, type="power_meter", brand="homewizard", meter_type=meter_type, phase=phase)


def _config(**categories: Any) -> Config:
    return Config(energy_provider="frank_energie", **categories)


class TestSystemCheckSensors:
    @patch("leo.__main__.get_power_meter")
    @patch("leo.__main__.get_price_provider")
    def test_no_sensors(self, mock_provider_fn: MagicMock, mock_get_meter: MagicMock) -> None:
        mock_provider_fn.return_value.get_future_prices.return_value = [MagicMock()]
        assert system_check(_config()) is True

    @patch("leo.__main__.get_power_meter")
    @patch("leo.__main__.get_price_provider")
    def test_sensor_ok(self, mock_provider_fn: MagicMock, mock_get_meter: MagicMock) -> None:
        mock_provider_fn.return_value.get_future_prices.return_value = [MagicMock()]

        config = _config(production=[_sensor("192.168.1.10", "kwh_3phase")])
        assert system_check(config) is True
        mock_get_meter.return_value.fetch.assert_called_once()

    @patch("leo.__main__.get_power_meter")
    @patch("leo.__main__.get_price_provider")
    def test_sensor_fetch_fails(self, mock_provider_fn: MagicMock, mock_get_meter: MagicMock) -> None:
        mock_provider_fn.return_value.get_future_prices.return_value = [MagicMock()]
        mock_get_meter.return_value.fetch.side_effect = FetchError("connection refused")

        config = _config(production=[_sensor("192.168.1.10", "kwh_3phase")])
        assert system_check(config) is False

    @patch("leo.__main__.get_power_meter")
    @patch("leo.__main__.get_price_provider")
    def test_partial_failure_checks_all(self, mock_provider_fn: MagicMock, mock_get_meter: MagicMock) -> None:
        mock_provider_fn.return_value.get_future_prices.return_value = [MagicMock()]

        ok_meter = MagicMock()
        fail_meter = MagicMock()
        fail_meter.fetch.side_effect = FetchError("connection refused")
        mock_get_meter.side_effect = [fail_meter, ok_meter]

        config = _config(
            production=[_sensor("192.168.1.10", "kwh_3phase")],
            nett_consumption=[_sensor("192.168.1.11", "p1")],
        )
        assert system_check(config) is False
        assert mock_get_meter.call_count == 2
