"""Tests for configuration loading."""

from pathlib import Path

import pytest
import yaml

from leo.config import Config, SensorsConfig, load_config
from leo.models.price_provider_config import PriceProviderConfig
from leo.models.temporal import TimeResolution
from leo.sensors.homewizard.config import (
    HomewizardPowerSensor1PhaseConfig,
    HomewizardPowerSensor3PhaseConfig,
)

FRANK_DICT = {"provider": "frank_energie", "time_resolution": 60}
FRANK = PriceProviderConfig(provider="frank_energie", time_resolution=TimeResolution.HOURLY)
P1_SENSOR_DICT = {"host": "192.168.1.11", "sensor_type": "power_meter", "brand": "homewizard", "meter_type": "p1"}
P1_SENSOR = HomewizardPowerSensor3PhaseConfig(
    host="192.168.1.11", sensor_type="power_meter", brand="homewizard", meter_type="p1"
)
MINIMAL_SENSORS_DICT = {"nett_consumption": P1_SENSOR_DICT, "production": [], "storage": []}
MINIMAL_SENSORS = SensorsConfig(nett_consumption=P1_SENSOR, production=[], storage=[])


@pytest.fixture()
def config_file(tmp_path: Path) -> Path:
    data = {"price_provider": FRANK_DICT, "sensors": MINIMAL_SENSORS_DICT}
    path = tmp_path / "config.yml"
    path.write_text(yaml.dump(data))
    return path


def test_load_config(config_file: Path) -> None:
    config = load_config(config_file)
    assert config.price_provider.provider == "frank_energie"
    assert config.sensors.nett_consumption.host == "192.168.1.11"


def test_missing_required_field(tmp_path: Path) -> None:
    path = tmp_path / "config.yml"
    path.write_text(yaml.dump({}))
    with pytest.raises(Exception):  # noqa: B017
        load_config(path)


def test_missing_sensors(tmp_path: Path) -> None:
    path = tmp_path / "config.yml"
    path.write_text(yaml.dump({"price_provider": FRANK_DICT}))
    with pytest.raises(Exception):  # noqa: B017
        load_config(path)


def test_invalid_provider(tmp_path: Path) -> None:
    path = tmp_path / "config.yml"
    path.write_text(
        yaml.dump(
            {
                "price_provider": {"provider": "nonexistent", "time_resolution": 60},
                "sensors": MINIMAL_SENSORS_DICT,
            }
        )
    )
    with pytest.raises(Exception):  # noqa: B017
        load_config(path)


def test_config_model_direct() -> None:
    config = Config(price_provider=FRANK, sensors=MINIMAL_SENSORS)
    assert config.price_provider.provider == "frank_energie"


def test_sensors_all_required() -> None:
    with pytest.raises(Exception):  # noqa: B017
        SensorsConfig(production=[], storage=[])  # type: ignore[call-arg]


def test_load_config_with_sensors(tmp_path: Path) -> None:
    data = {
        "price_provider": FRANK_DICT,
        "sensors": {
            "nett_consumption": P1_SENSOR_DICT,
            "production": [
                {
                    "host": "192.168.1.10",
                    "sensor_type": "power_meter",
                    "brand": "homewizard",
                    "meter_type": "kwh_3phase",
                }
            ],
            "storage": [
                {
                    "host": "192.168.1.12",
                    "sensor_type": "power_meter",
                    "brand": "homewizard",
                    "meter_type": "kwh_1phase",
                    "phase": 2,
                },
                {
                    "host": "192.168.1.13",
                    "sensor_type": "power_meter",
                    "brand": "homewizard",
                    "meter_type": "power_socket",
                    "phase": 1,
                },
            ],
        },
    }
    path = tmp_path / "config.yml"
    path.write_text(yaml.dump(data))
    config = load_config(path)

    assert config.sensors.nett_consumption.host == "192.168.1.11"

    assert len(config.sensors.production) == 1
    assert config.sensors.production[0].host == "192.168.1.10"
    assert config.sensors.production[0].meter_type == "kwh_3phase"

    assert len(config.sensors.storage) == 2
    assert isinstance(config.sensors.storage[0], HomewizardPowerSensor1PhaseConfig)
    assert config.sensors.storage[0].phase == 2
    assert config.sensors.storage[1].meter_type == "power_socket"


def test_invalid_sensor_type(tmp_path: Path) -> None:
    data = {
        "price_provider": FRANK_DICT,
        "sensors": {
            "nett_consumption": P1_SENSOR_DICT,
            "production": [
                {
                    "host": "192.168.1.10",
                    "sensor_type": "power_meter",
                    "brand": "homewizard",
                    "meter_type": "nonexistent",
                }
            ],
            "storage": [],
        },
    }
    path = tmp_path / "config.yml"
    path.write_text(yaml.dump(data))
    with pytest.raises(Exception):  # noqa: B017
        load_config(path)


def test_sensor_missing_host() -> None:
    with pytest.raises(Exception):  # noqa: B017
        HomewizardPowerSensor3PhaseConfig(sensor_type="power_meter", brand="homewizard", meter_type="p1")  # type: ignore[call-arg]


def test_sensor_config_direct() -> None:
    cfg = HomewizardPowerSensor1PhaseConfig(
        host="192.168.1.10", sensor_type="power_meter", brand="homewizard", meter_type="kwh_1phase", phase=3
    )
    assert cfg.host == "192.168.1.10"
    assert cfg.meter_type == "kwh_1phase"
    assert cfg.phase == 3


def test_sensor_config_3phase() -> None:
    cfg = HomewizardPowerSensor3PhaseConfig(
        host="192.168.1.10", sensor_type="power_meter", brand="homewizard", meter_type="p1"
    )
    assert cfg.host == "192.168.1.10"
    assert cfg.meter_type == "p1"
