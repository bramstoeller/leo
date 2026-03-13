"""Configuration loading from YAML."""

from pathlib import Path

import yaml
from pydantic import BaseModel

from leo.models.temporal import TimeResolution
from leo.providers import EnergyProvider

DEFAULT_CONFIG_PATH = Path("config.yml")


class Config(BaseModel):
    energy_provider: EnergyProvider
    time_resolution: TimeResolution = TimeResolution.HOURLY


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> Config:
    """Load configuration from a YAML file."""
    raw = yaml.safe_load(path.read_text())
    return Config.model_validate(raw)
