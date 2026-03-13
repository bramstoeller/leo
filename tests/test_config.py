"""Tests for configuration loading."""

from pathlib import Path

import pytest
import yaml

from leo.config import Config, load_config
from leo.providers import EnergyProvider


@pytest.fixture()
def config_file(tmp_path: Path) -> Path:
    data = {"energy_provider": "frank_energie"}
    path = tmp_path / "config.yml"
    path.write_text(yaml.dump(data))
    return path


def test_load_config(config_file: Path) -> None:
    config = load_config(config_file)
    assert config.energy_provider == EnergyProvider.FRANK_ENERGIE


def test_missing_required_field(tmp_path: Path) -> None:
    path = tmp_path / "config.yml"
    path.write_text(yaml.dump({}))
    with pytest.raises(Exception):  # noqa: B017
        load_config(path)


def test_invalid_provider(tmp_path: Path) -> None:
    path = tmp_path / "config.yml"
    path.write_text(yaml.dump({"energy_provider": "nonexistent"}))
    with pytest.raises(Exception):  # noqa: B017
        load_config(path)


def test_config_model_direct() -> None:
    config = Config(energy_provider=EnergyProvider.FRANK_ENERGIE)
    assert config.energy_provider == "frank_energie"
