"""Configuration loading from YAML."""

from pathlib import Path

import yaml
from pydantic import BaseModel

from leo.models.price_provider_config import PriceProviderConfig
from leo.sensors.homewizard.config import HomeWizardSensorConfig

DEFAULT_CONFIG_PATH = Path("config.yml")

# When adding a new brand, add its config type to this union and discriminate on "brand":
# SensorConfig = Annotated[HomeWizardSensorConfig | OtherBrandConfig, Discriminator("brand")]
SensorConfig = HomeWizardSensorConfig


class SensorsConfig(BaseModel):
    nett_consumption: SensorConfig
    production: list[SensorConfig]
    storage: list[SensorConfig]


class Config(BaseModel):
    price_provider: PriceProviderConfig
    sensors: SensorsConfig


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> Config:
    """Load configuration from a YAML file."""
    raw = yaml.safe_load(path.read_text())
    return Config.model_validate(raw)
