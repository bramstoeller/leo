from enum import IntEnum


class TimeResolution(IntEnum):
    """Time resolution in minutes."""

    QUARTER_HOUR = 15
    HOURLY = 60

    def slots_per_day(self) -> int:
        """Number of slots that fit in a 24-hour day."""
        return 24 * 60 // self.value
