"""Configuration loading from YAML."""

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel

from leo.meters import MeterBrand
from leo.meters.homewizard import HomeWizardMeterType
from leo.models.temporal import TimeResolution
from leo.prices import EnergyProvider

DEFAULT_CONFIG_PATH = Path("config.yml")

CATEGORIES = ("nett_consumption", "production", "batteries", "boilers")

SensorType = Literal["power_meter"]


class SensorConfig(BaseModel):
    host: str
    type: SensorType
    brand: MeterBrand
    meter_type: HomeWizardMeterType
    phase: int | None = None


class Config(BaseModel):
    energy_provider: EnergyProvider
    time_resolution: TimeResolution = TimeResolution.HOURLY
    nett_consumption: list[SensorConfig] = []
    production: list[SensorConfig] = []
    batteries: list[SensorConfig] = []
    boilers: list[SensorConfig] = []


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> Config:
    """Load configuration from a YAML file."""
    raw = yaml.safe_load(path.read_text())
    return Config.model_validate(raw)
