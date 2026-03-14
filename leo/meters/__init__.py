from typing import Any, Literal

from leo.meters.homewizard import HomeWizardMeterType
from leo.meters.power_meter import PowerMeter

MeterBrand = Literal["homewizard"]

MeterType = HomeWizardMeterType


def get_power_meter(brand: MeterBrand, meter_type: MeterType, **kwargs: Any) -> PowerMeter:
    if brand == "homewizard":
        from leo.meters.homewizard import get_hw_power_meter

        return get_hw_power_meter(meter_type, **kwargs)

    raise ValueError(f"Unknown power meter brand: {brand}")
