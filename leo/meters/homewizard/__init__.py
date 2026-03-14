from typing import Any, Literal

from leo.meters.homewizard.power_meter import (
    HomeWizardPowerMeter,
    HomeWizardPowerMeter1Phase,
    HomeWizardPowerMeter3Phase,
)

HomeWizardMeterType = Literal["p1", "kwh_3phase", "kwh_1phase", "power_socket"]


def get_hw_power_meter(meter_type: HomeWizardMeterType, **kwargs: Any) -> HomeWizardPowerMeter:
    if "host" not in kwargs:
        raise ValueError("Missing required argument: host")
    if not isinstance(kwargs["host"], str):
        raise ValueError("Argument 'host' must be a string")

    if meter_type in ("p1", "kwh_3phase"):
        return HomeWizardPowerMeter3Phase(host=kwargs["host"])

    if meter_type in ("kwh_1phase", "power_socket"):
        if "phase" not in kwargs:
            raise ValueError("Missing required argument: phase")
        if not isinstance(kwargs["phase"], int):
            raise ValueError("Argument 'phase' must be an integer")
        return HomeWizardPowerMeter1Phase(host=kwargs["host"], phase=kwargs["phase"])

    raise ValueError(f"Unknown HomeWizard power meter type: {meter_type}")
