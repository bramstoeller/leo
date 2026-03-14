from typing import Any, Literal

from leo.sensors.homewizard.power_meter import (
    HomeWizardPowerMeter,
    HomeWizardPowerMeter1Phase,
    HomeWizardPowerMeter3Phase,
)

HomeWizardMeterType = Literal["p1", "kwh_3phase", "kwh_1phase", "power_socket"]


def get_hw_power_meter(meter_type: HomeWizardMeterType, host: str, **kwargs: Any) -> HomeWizardPowerMeter:
    if meter_type in ("p1", "kwh_3phase"):
        return HomeWizardPowerMeter3Phase(host=host)

    if meter_type in ("kwh_1phase", "power_socket"):
        if "phase" not in kwargs:
            raise ValueError("Phase must be specified for 1-phase meters")
        if not isinstance(kwargs["phase"], int):
            raise ValueError("Phase must be an integer for 1-phase meters")
        return HomeWizardPowerMeter1Phase(host=host, phase=kwargs["phase"])

    raise ValueError(f"Unknown HomeWizard power meter type: {meter_type}")
