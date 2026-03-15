"""Tests for energy readings import with atomic transactions."""

import sqlite3
from pathlib import Path

import pytest

from leo.db import connect
from leo.models.electrical import EnergyUnit
from leo.tools.import_readings import _import_readings, _read_csv

_HEADER = "timestamp_from,timestamp_till,import_kwh,export_kwh"


def _write_csv(tmp_path: Path, name: str, *rows: str) -> Path:
    path = tmp_path / name
    path.write_text("\n".join(rows) + "\n")
    return path


async def _count_readings(db_path: Path) -> int:
    db = await connect(db_path)
    cursor = await db.execute("SELECT COUNT(*) FROM energy_readings")
    row = await cursor.fetchone()
    await db.close()
    assert row is not None
    return int(row[0])


class TestImportReadings:
    async def test_import_fresh(self, tmp_path: Path) -> None:
        csv_path = _write_csv(
            tmp_path,
            "readings.csv",
            _HEADER,
            "2024-01-01T00:00:00+01:00,2024-01-01T00:15:00+01:00,0.5,0.2",
            "2024-01-01T00:15:00+01:00,2024-01-01T00:30:00+01:00,0.3,0.1",
        )
        db_path = tmp_path / "test.db"
        rows = _read_csv(csv_path)

        total = await _import_readings("sensor.1", rows, db_path, overwrite=False)

        assert total == 2
        assert await _count_readings(db_path) == 2

    async def test_stores_values_in_joules(self, tmp_path: Path) -> None:
        csv_path = _write_csv(
            tmp_path,
            "readings.csv",
            _HEADER,
            "2024-01-01T00:00:00+01:00,2024-01-01T00:15:00+01:00,1.0,0.5",
        )
        db_path = tmp_path / "test.db"
        rows = _read_csv(csv_path)

        await _import_readings("sensor.1", rows, db_path, overwrite=False)

        db = await connect(db_path)
        cursor = await db.execute("SELECT import_total, export_total, unit FROM energy_readings")
        row = await cursor.fetchone()
        await db.close()
        assert row is not None
        assert row[0] == pytest.approx(1.0 * EnergyUnit.KWH.multiplier)  # 3_600_000
        assert row[1] == pytest.approx(0.5 * EnergyUnit.KWH.multiplier)  # 1_800_000
        assert row[2] == str(EnergyUnit.J)

    async def test_duplicate_fails_without_overwrite(self, tmp_path: Path) -> None:
        csv_path = _write_csv(
            tmp_path,
            "readings.csv",
            _HEADER,
            "2024-01-01T00:00:00+01:00,2024-01-01T00:15:00+01:00,0.5,0.2",
        )
        db_path = tmp_path / "test.db"
        rows = _read_csv(csv_path)

        await _import_readings("sensor.1", rows, db_path, overwrite=False)

        with pytest.raises(sqlite3.IntegrityError):
            await _import_readings("sensor.1", rows, db_path, overwrite=False)

        assert await _count_readings(db_path) == 1

    async def test_duplicate_succeeds_with_overwrite(self, tmp_path: Path) -> None:
        csv_path = _write_csv(
            tmp_path,
            "readings.csv",
            _HEADER,
            "2024-01-01T00:00:00+01:00,2024-01-01T00:15:00+01:00,0.5,0.2",
        )
        db_path = tmp_path / "test.db"
        rows = _read_csv(csv_path)

        await _import_readings("sensor.1", rows, db_path, overwrite=False)
        await _import_readings("sensor.1", rows, db_path, overwrite=True)

        assert await _count_readings(db_path) == 1

    async def test_rollback_on_partial_duplicate(self, tmp_path: Path) -> None:
        """First record exists, second is new — entire batch should be rolled back."""
        csv1 = _write_csv(
            tmp_path,
            "batch1.csv",
            _HEADER,
            "2024-01-01T00:00:00+01:00,2024-01-01T00:15:00+01:00,0.5,0.2",
        )
        csv2 = _write_csv(
            tmp_path,
            "batch2.csv",
            _HEADER,
            "2024-01-01T00:00:00+01:00,2024-01-01T00:15:00+01:00,0.5,0.2",
            "2024-01-01T00:15:00+01:00,2024-01-01T00:30:00+01:00,0.3,0.1",
        )
        db_path = tmp_path / "test.db"

        await _import_readings("sensor.1", _read_csv(csv1), db_path, overwrite=False)

        with pytest.raises(sqlite3.IntegrityError):
            await _import_readings("sensor.1", _read_csv(csv2), db_path, overwrite=False)

        # Only the first batch's record should exist
        assert await _count_readings(db_path) == 1

    async def test_different_sensors_no_conflict(self, tmp_path: Path) -> None:
        csv_path = _write_csv(
            tmp_path,
            "readings.csv",
            _HEADER,
            "2024-01-01T00:00:00+01:00,2024-01-01T00:15:00+01:00,0.5,0.2",
        )
        db_path = tmp_path / "test.db"
        rows = _read_csv(csv_path)

        await _import_readings("sensor.1", rows, db_path, overwrite=False)
        await _import_readings("sensor.2", rows, db_path, overwrite=False)

        assert await _count_readings(db_path) == 2
