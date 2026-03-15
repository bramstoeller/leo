from datetime import timedelta
from enum import IntEnum


class TimeResolution(IntEnum):
    """Time resolution in minutes."""

    QUARTER_HOUR = 15
    HOURLY = 60

    def slot_duration(self) -> timedelta:
        """Duration of a single time slot."""
        return timedelta(minutes=self.value)

    def slots_per_day(self) -> int:
        """Number of slots that fit in a 24-hour day."""
        return 24 * 60 // self.value
