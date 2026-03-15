from typing import Annotated, Literal

from pydantic import Discriminator

from leo.sensors.config import SensorConfig


class HomewizardPowerSensor3PhaseConfig(SensorConfig):
    sensor_type: Literal["power_meter"]
    brand: Literal["homewizard"]
    meter_type: Literal["p1", "kwh_3phase"]
    host: str

    def __str__(self) -> str:
        return self.name or f"{super().__str__()}.{self.meter_type}[{self.host}]"


class HomewizardPowerSensor1PhaseConfig(SensorConfig):
    sensor_type: Literal["power_meter"]
    brand: Literal["homewizard"]
    meter_type: Literal["kwh_1phase", "power_socket"]
    host: str
    phase: int

    def __str__(self) -> str:
        return self.name or f"{super().__str__()}.{self.meter_type}[{self.host}]"


HomeWizardSensorConfig = Annotated[
    HomewizardPowerSensor3PhaseConfig | HomewizardPowerSensor1PhaseConfig,
    Discriminator("meter_type"),
]
