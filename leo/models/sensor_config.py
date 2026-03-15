from pydantic import BaseModel

from leo.sensors.config import SensorBrand, SensorType


class SensorConfig(BaseModel):
    name: str | None = None
    sensor_type: SensorType
    brand: SensorBrand

    def __str__(self) -> str:
        return self.name or f"{self.brand}.{self.sensor_type}"
