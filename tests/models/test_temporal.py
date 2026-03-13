"""Tests for time resolution enum."""

from leo.models.temporal import TimeResolution


class TestTimeResolution:
    def test_quarter_hour_fits_96_times_in_day(self) -> None:
        assert TimeResolution.QUARTER_HOUR.slots_per_day() == 96

    def test_hourly_fits_24_times_in_day(self) -> None:
        assert TimeResolution.HOURLY.slots_per_day() == 24
