"""Tests for configuration loading."""

from pathlib import Path

import pytest
import yaml

from leo.config import Config, load_config
from leo.sensors.homewizard.config import HomewizardPowerSensor1PhaseConfig, HomewizardPowerSensor3PhaseConfig


@pytest.fixture()
def config_file(tmp_path: Path) -> Path:
    data = {"price_provider": "frank_energie"}
    path = tmp_path / "config.yml"
    path.write_text(yaml.dump(data))
    return path


def test_load_config(config_file: Path) -> None:
    config = load_config(config_file)
    assert config.price_provider == "frank_energie"


def test_missing_required_field(tmp_path: Path) -> None:
    path = tmp_path / "config.yml"
    path.write_text(yaml.dump({}))
    with pytest.raises(Exception):  # noqa: B017
        load_config(path)


def test_invalid_provider(tmp_path: Path) -> None:
    path = tmp_path / "config.yml"
    path.write_text(yaml.dump({"price_provider": "nonexistent"}))
    with pytest.raises(Exception):  # noqa: B017
        load_config(path)


def test_config_model_direct() -> None:
    config = Config(price_provider="frank_energie")
    assert config.price_provider == "frank_energie"


def test_categories_default_empty() -> None:
    config = Config(price_provider="frank_energie")
    assert config.nett_consumption == []
    assert config.production == []
    assert config.batteries == []
    assert config.boilers == []


def test_load_config_with_sensors(tmp_path: Path) -> None:
    data = {
        "price_provider": "frank_energie",
        "nett_consumption": [
            {"host": "192.168.1.11", "sensor_type": "power_meter", "brand": "homewizard", "meter_type": "p1"}
        ],
        "production": [
            {"host": "192.168.1.10", "sensor_type": "power_meter", "brand": "homewizard", "meter_type": "kwh_3phase"}
        ],
        "batteries": [
            {
                "host": "192.168.1.12",
                "sensor_type": "power_meter",
                "brand": "homewizard",
                "meter_type": "kwh_1phase",
                "phase": 2,
            }
        ],
        "boilers": [
            {
                "host": "192.168.1.13",
                "sensor_type": "power_meter",
                "brand": "homewizard",
                "meter_type": "power_socket",
                "phase": 1,
            }
        ],
    }
    path = tmp_path / "config.yml"
    path.write_text(yaml.dump(data))
    config = load_config(path)

    assert len(config.production) == 1
    assert config.production[0].host == "192.168.1.10"
    assert config.production[0].meter_type == "kwh_3phase"

    assert len(config.batteries) == 1
    assert isinstance(config.batteries[0], HomewizardPowerSensor1PhaseConfig)
    assert config.batteries[0].phase == 2

    assert len(config.boilers) == 1
    assert config.boilers[0].meter_type == "power_socket"


def test_invalid_sensor_type(tmp_path: Path) -> None:
    data = {
        "price_provider": "frank_energie",
        "production": [
            {"host": "192.168.1.10", "sensor_type": "power_meter", "brand": "homewizard", "meter_type": "nonexistent"}
        ],
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
