from typing import Annotated, Literal

from pydantic import Discriminator

from leo.models.sensor_config import SensorConfig


class HomewizardPowerSensor3PhaseConfig(SensorConfig):
    sensor_type: Literal["power_meter"]
    brand: Literal["homewizard"]
    meter_type: Literal["p1", "kwh_3phase"]
    host: str


class HomewizardPowerSensor1PhaseConfig(SensorConfig):
    sensor_type: Literal["power_meter"]
    brand: Literal["homewizard"]
    meter_type: Literal["kwh_1phase", "power_socket"]
    host: str
    phase: int


HomeWizardSensorConfig = Annotated[
    HomewizardPowerSensor3PhaseConfig | HomewizardPowerSensor1PhaseConfig,
    Discriminator("meter_type"),
]
