from typing import Literal

from pydantic import BaseModel

SensorType = Literal["power_meter"]
SensorBrand = Literal["homewizard"]


class SensorConfig(BaseModel):
    name: str | None = None
    sensor_type: SensorType
    brand: SensorBrand

    def __str__(self) -> str:
        return self.name or f"{self.brand}.{self.sensor_type}"
