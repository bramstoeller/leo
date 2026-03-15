"""Tests for system_check sensor verification."""

from typing import Literal
from unittest.mock import AsyncMock, MagicMock, patch

from leo.config import Config, SensorConfig, SensorsConfig
from leo.exceptions import FetchError
from leo.models.temporal import TimeResolution
from leo.prices.config import PriceProviderConfig
from leo.sensors.homewizard.config import HomewizardPowerSensor3PhaseConfig
from leo.system_check import system_check

HW3PhaseMeterType = Literal["p1", "kwh_3phase"]

FRANK = PriceProviderConfig(provider="frank_energie", time_resolution=TimeResolution.HOURLY)
P1_SENSOR = HomewizardPowerSensor3PhaseConfig(
    host="192.168.1.11", sensor_type="power_meter", brand="homewizard", meter_type="p1"
)


def _sensor(host: str, meter_type: HW3PhaseMeterType) -> HomewizardPowerSensor3PhaseConfig:
    return HomewizardPowerSensor3PhaseConfig(
        host=host, sensor_type="power_meter", brand="homewizard", meter_type=meter_type
    )


def _config(
    nett_consumption: SensorConfig = P1_SENSOR,
    production: list[SensorConfig] | None = None,
    storage: list[SensorConfig] | None = None,
) -> Config:
    return Config(
        price_provider=FRANK,
        sensors=SensorsConfig(
            nett_consumption=nett_consumption,
            production=production or [],
            storage=storage or [],
        ),
    )


class TestSystemCheckSensors:
    @patch("leo.system_check.get_power_meter")
    @patch("leo.system_check.get_price_provider")
    async def test_no_sensors(self, mock_provider_fn: MagicMock, mock_get_meter: MagicMock) -> None:
        mock_provider_fn.return_value.get_future_prices = AsyncMock(return_value=[MagicMock()])
        mock_get_meter.return_value.sensor_id = AsyncMock(return_value="hw.001")
        assert await system_check(_config()) is True

    @patch("leo.system_check.get_power_meter")
    @patch("leo.system_check.get_price_provider")
    async def test_sensor_ok(self, mock_provider_fn: MagicMock, mock_get_meter: MagicMock) -> None:
        mock_provider_fn.return_value.get_future_prices = AsyncMock(return_value=[MagicMock()])
        mock_get_meter.return_value.sensor_id = AsyncMock(return_value="hw.001")

        config = _config(production=[_sensor("192.168.1.10", "kwh_3phase")])
        assert await system_check(config) is True
        assert mock_get_meter.return_value.sensor_id.call_count == 2  # nett_consumption + production

    @patch("leo.system_check.get_power_meter")
    @patch("leo.system_check.get_price_provider")
    async def test_sensor_fetch_fails(self, mock_provider_fn: MagicMock, mock_get_meter: MagicMock) -> None:
        mock_provider_fn.return_value.get_future_prices = AsyncMock(return_value=[MagicMock()])
        mock_get_meter.return_value.sensor_id = AsyncMock(side_effect=FetchError("connection refused"))

        config = _config(production=[_sensor("192.168.1.10", "kwh_3phase")])
        assert await system_check(config) is False

    @patch("leo.system_check.get_power_meter")
    @patch("leo.system_check.get_price_provider")
    async def test_partial_failure_checks_all(self, mock_provider_fn: MagicMock, mock_get_meter: MagicMock) -> None:
        mock_provider_fn.return_value.get_future_prices = AsyncMock(return_value=[MagicMock()])

        ok_meter = MagicMock()
        ok_meter.sensor_id = AsyncMock(return_value="hw.ok")
        fail_meter = MagicMock()
        fail_meter.sensor_id = AsyncMock(side_effect=FetchError("connection refused"))
        mock_get_meter.side_effect = [ok_meter, fail_meter, ok_meter]

        config = _config(
            production=[_sensor("192.168.1.10", "kwh_3phase")],
            storage=[_sensor("192.168.1.12", "kwh_3phase")],
        )
        assert await system_check(config) is False
        assert mock_get_meter.call_count == 3  # nett_consumption + production + storage
