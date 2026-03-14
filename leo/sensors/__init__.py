from typing import Any

from leo.sensors.config import SensorBrand
from leo.sensors.power_meter import PowerMeter


def get_power_meter(brand: SensorBrand, **kwargs: Any) -> PowerMeter:
    if brand == "homewizard":
        from leo.sensors.homewizard import get_hw_power_meter

        return get_hw_power_meter(**kwargs)

    raise ValueError(f"Unknown power meter brand: {brand}")
