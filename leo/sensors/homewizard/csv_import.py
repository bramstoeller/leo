"""Import HomeWizard Energy+ CSV exports into EnergyReadingSlot entries.

HomeWizard CSV format (15-min interval, P1 meter):

    time,Import T1 kWh,Import T2 kWh,Export T1 kWh,Export T2 kWh,L1 max W,L2 max W,L3 max W
    2024-01-01 00:15,123.456,789.012,45.678,12.345,1200,800,600

Values are cumulative meter readings (not deltas). This module computes
the delta between consecutive rows to produce per-slot import/export energy.
The L1/L2/L3 max W columns are peak power, not energy - they are ignored.
"""

import csv
from datetime import datetime
from itertools import pairwise
from pathlib import Path

from leo.models.electrical import Energy, EnergyUnit
from leo.models.energy_reading import EnergyReadingSlot

# Required columns (L1/L2/L3 max W are optional)
_IMPORT_T1 = "Import T1 kWh"
_IMPORT_T2 = "Import T2 kWh"
_EXPORT_T1 = "Export T1 kWh"
_EXPORT_T2 = "Export T2 kWh"
_TIME = "time"

_REQUIRED_COLUMNS = {_TIME, _IMPORT_T1, _IMPORT_T2, _EXPORT_T1, _EXPORT_T2}


def _parse_timestamp(value: str) -> datetime:
    """Parse a HomeWizard timestamp, assuming local time if no timezone."""
    value = value.strip()
    try:
        dt = datetime.strptime(value, "%Y-%m-%d %H:%M")
    except ValueError:
        dt = datetime.strptime(value, "%Y-%m-%d")
    return dt.astimezone()


def _parse_float(value: str) -> float:
    return float(value.strip())


def import_csv(path: Path, sensor_id: str) -> list[EnergyReadingSlot]:
    """Import a HomeWizard Energy+ CSV export file.

    Args:
        path: Path to the CSV file.
        sensor_id: Identifier for the sensor (e.g. serial number).

    Returns:
        List of EnergyReadingSlot entries, one per interval.

    Raises:
        ValueError: If the CSV is missing required columns or has no data rows.
    """
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        if reader.fieldnames is None:
            raise ValueError(f"CSV file has no header: {path}")

        missing = _REQUIRED_COLUMNS - set(reader.fieldnames)
        if missing:
            raise ValueError(f"CSV missing required columns: {missing}")

        rows = list(reader)

    if len(rows) < 2:
        raise ValueError("CSV needs at least 2 rows to compute deltas")

    slots: list[EnergyReadingSlot] = []
    for prev_row, cur_row in pairwise(rows):
        timestamp_from = _parse_timestamp(prev_row[_TIME])
        timestamp_till = _parse_timestamp(cur_row[_TIME])

        import_delta = (
            _parse_float(cur_row[_IMPORT_T1])
            - _parse_float(prev_row[_IMPORT_T1])
            + _parse_float(cur_row[_IMPORT_T2])
            - _parse_float(prev_row[_IMPORT_T2])
        )
        export_delta = (
            _parse_float(cur_row[_EXPORT_T1])
            - _parse_float(prev_row[_EXPORT_T1])
            + _parse_float(cur_row[_EXPORT_T2])
            - _parse_float(prev_row[_EXPORT_T2])
        )

        slots.append(
            EnergyReadingSlot(
                sensor_id=sensor_id,
                timestamp_from=timestamp_from,
                timestamp_till=timestamp_till,
                import_total=Energy(value=round(import_delta, 6), unit=EnergyUnit.KWH),
                export_total=Energy(value=round(export_delta, 6), unit=EnergyUnit.KWH),
            )
        )

    return slots
