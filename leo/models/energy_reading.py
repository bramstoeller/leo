from pydantic import AwareDatetime, BaseModel

from leo.models.electrical import Energy


class EnergyReadingSlot(BaseModel):
    """Energy imported and exported by a sensor during a time slot."""

    timestamp_from: AwareDatetime
    timestamp_till: AwareDatetime
    import_total: Energy
    export_total: Energy

    def __str__(self) -> str:
        dt_from = self.timestamp_from.astimezone()
        dt_till = self.timestamp_till.astimezone()
        return (
            f"{dt_from.date()} {dt_from.time()}-{dt_till.time()} import={self.import_total} export={self.export_total}"
        )
