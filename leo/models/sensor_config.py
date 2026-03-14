from pydantic import BaseModel

from leo.sensors.config import SensorBrand, SensorType


class SensorConfig(BaseModel):
    sensor_type: SensorType
    brand: SensorBrand
