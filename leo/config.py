"""Configuration loading from YAML."""

from pathlib import Path

import yaml
from pydantic import BaseModel

from leo.models.temporal import TimeResolution
from leo.prices.config import PriceProviderName
from leo.sensors.homewizard.config import HomeWizardSensorConfig

DEFAULT_CONFIG_PATH = Path("config.yml")

CATEGORIES = ("nett_consumption", "production", "batteries", "boilers")

# When adding a new brand, add its config type to this union and discriminate on "brand":
# SensorConfig = Annotated[HomeWizardSensorConfig | OtherBrandConfig, Discriminator("brand")]
SensorConfig = HomeWizardSensorConfig


class Config(BaseModel):
    price_provider: PriceProviderName
    time_resolution: TimeResolution = TimeResolution.HOURLY
    nett_consumption: list[SensorConfig] = []
    production: list[SensorConfig] = []
    batteries: list[SensorConfig] = []
    boilers: list[SensorConfig] = []


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> Config:
    """Load configuration from a YAML file."""
    raw = yaml.safe_load(path.read_text())
    return Config.model_validate(raw)
