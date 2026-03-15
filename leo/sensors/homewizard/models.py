from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from leo.models.electrical import Energy, EnergyUnit, Power, PowerUnit


class DeviceInfo(BaseModel):
    model_config = ConfigDict(extra="ignore")

    serial_number: str = Field(alias="serial")
    product_type: str
    product_name: str


class PowerMeterData(BaseModel):
    model_config = ConfigDict(extra="ignore")

    total_power_import_kwh: float | None = None
    total_power_export_kwh: float | None = None
    active_power_l1_w: float | None = None
    active_power_l2_w: float | None = None
    active_power_l3_w: float | None = None

    @property
    def total_import(self) -> Energy | None:
        if self.total_power_import_kwh is None:
            return None
        return Energy(value=self.total_power_import_kwh, unit=EnergyUnit.KWH)

    @property
    def total_export(self) -> Energy | None:
        if self.total_power_export_kwh is None:
            return None
        return Energy(value=self.total_power_export_kwh, unit=EnergyUnit.KWH)

    @property
    def active_power_l1(self) -> Power | None:
        if self.active_power_l1_w is None:
            return None
        return Power(value=self.active_power_l1_w, unit=PowerUnit.W)

    @property
    def active_power_l2(self) -> Power | None:
        if self.active_power_l2_w is None:
            return None
        return Power(value=self.active_power_l2_w, unit=PowerUnit.W)

    @property
    def active_power_l3(self) -> Power | None:
        if self.active_power_l3_w is None:
            return None
        return Power(value=self.active_power_l3_w, unit=PowerUnit.W)
