from pydantic import AwareDatetime, BaseModel

from leo.models.electrical import Energy


class EnergyReadingSlot(BaseModel):
    """Energy imported and exported by a sensor during a time slot, per phase and total."""

    sensor_id: str
    timestamp_from: AwareDatetime
    timestamp_till: AwareDatetime
    import_total: Energy
    import_l1: Energy | None = None
    import_l2: Energy | None = None
    import_l3: Energy | None = None
    export_total: Energy
    export_l1: Energy | None = None
    export_l2: Energy | None = None
    export_l3: Energy | None = None

    def __str__(self) -> str:
        dt_from = self.timestamp_from.astimezone()
        dt_till = self.timestamp_till.astimezone()
        return (
            f"{dt_from.date()} {dt_from.time()}-{dt_till.time()}"
            f" [{self.sensor_id}] import={self.import_total} export={self.export_total}"
        )
