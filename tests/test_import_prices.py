"""Tests for energy prices import with atomic transactions."""

import sqlite3
from pathlib import Path

import pytest

from leo.db import connect
from leo.tools.import_prices import _import_prices, _read_csv

_HEADER = "timestamp_from,timestamp_till,price_eur_kwh"


def _write_csv(tmp_path: Path, name: str, *rows: str) -> Path:
    path = tmp_path / name
    path.write_text("\n".join(rows) + "\n")
    return path


async def _count_prices(db_path: Path) -> int:
    db = await connect(db_path)
    cursor = await db.execute("SELECT COUNT(*) FROM energy_prices")
    row = await cursor.fetchone()
    await db.close()
    assert row is not None
    return int(row[0])


class TestImportPrices:
    async def test_import_fresh(self, tmp_path: Path) -> None:
        csv_path = _write_csv(
            tmp_path,
            "prices.csv",
            _HEADER,
            "2024-01-01T00:00:00+00:00,2024-01-01T00:15:00+00:00,0.25",
            "2024-01-01T00:15:00+00:00,2024-01-01T00:30:00+00:00,0.30",
        )
        db_path = tmp_path / "test.db"
        rows, price_col, currency, energy_unit = _read_csv(csv_path)

        total = await _import_prices("frank_energie", rows, price_col, currency, energy_unit, db_path, overwrite=False)

        assert total == 2
        assert await _count_prices(db_path) == 2

    async def test_detects_currency_and_unit(self, tmp_path: Path) -> None:
        csv_path = _write_csv(
            tmp_path,
            "prices.csv",
            "timestamp_from,timestamp_till,price_usd_mwh",
            "2024-01-01T00:00:00+00:00,2024-01-01T00:15:00+00:00,25.0",
        )
        db_path = tmp_path / "test.db"
        rows, price_col, currency, energy_unit = _read_csv(csv_path)

        assert price_col == "price_usd_mwh"
        assert currency == "USD"
        assert energy_unit == "mwh"

        await _import_prices("provider", rows, price_col, currency, energy_unit, db_path, overwrite=False)

        db = await connect(db_path)
        cursor = await db.execute("SELECT currency, energy_unit FROM energy_prices")
        row = await cursor.fetchone()
        await db.close()
        assert row is not None
        assert row[0] == "USD"
        assert row[1] == "mwh"

    async def test_duplicate_fails_without_overwrite(self, tmp_path: Path) -> None:
        csv_path = _write_csv(
            tmp_path,
            "prices.csv",
            _HEADER,
            "2024-01-01T00:00:00+00:00,2024-01-01T00:15:00+00:00,0.25",
        )
        db_path = tmp_path / "test.db"
        rows, price_col, currency, energy_unit = _read_csv(csv_path)

        await _import_prices("frank_energie", rows, price_col, currency, energy_unit, db_path, overwrite=False)

        with pytest.raises(sqlite3.IntegrityError):
            await _import_prices("frank_energie", rows, price_col, currency, energy_unit, db_path, overwrite=False)

        assert await _count_prices(db_path) == 1

    async def test_duplicate_succeeds_with_overwrite(self, tmp_path: Path) -> None:
        csv_path = _write_csv(
            tmp_path,
            "prices.csv",
            _HEADER,
            "2024-01-01T00:00:00+00:00,2024-01-01T00:15:00+00:00,0.25",
        )
        db_path = tmp_path / "test.db"
        rows, price_col, currency, energy_unit = _read_csv(csv_path)

        await _import_prices("frank_energie", rows, price_col, currency, energy_unit, db_path, overwrite=False)
        await _import_prices("frank_energie", rows, price_col, currency, energy_unit, db_path, overwrite=True)

        assert await _count_prices(db_path) == 1

    async def test_rollback_on_partial_duplicate(self, tmp_path: Path) -> None:
        csv1 = _write_csv(
            tmp_path,
            "batch1.csv",
            _HEADER,
            "2024-01-01T00:00:00+00:00,2024-01-01T00:15:00+00:00,0.25",
        )
        csv2 = _write_csv(
            tmp_path,
            "batch2.csv",
            _HEADER,
            "2024-01-01T00:00:00+00:00,2024-01-01T00:15:00+00:00,0.25",
            "2024-01-01T00:15:00+00:00,2024-01-01T00:30:00+00:00,0.30",
        )
        db_path = tmp_path / "test.db"

        rows1, pc1, c1, u1 = _read_csv(csv1)
        await _import_prices("frank_energie", rows1, pc1, c1, u1, db_path, overwrite=False)

        rows2, pc2, c2, u2 = _read_csv(csv2)
        with pytest.raises(sqlite3.IntegrityError):
            await _import_prices("frank_energie", rows2, pc2, c2, u2, db_path, overwrite=False)

        assert await _count_prices(db_path) == 1

    async def test_different_providers_no_conflict(self, tmp_path: Path) -> None:
        csv_path = _write_csv(
            tmp_path,
            "prices.csv",
            _HEADER,
            "2024-01-01T00:00:00+00:00,2024-01-01T00:15:00+00:00,0.25",
        )
        db_path = tmp_path / "test.db"
        rows, price_col, currency, energy_unit = _read_csv(csv_path)

        await _import_prices("provider_a", rows, price_col, currency, energy_unit, db_path, overwrite=False)
        await _import_prices("provider_b", rows, price_col, currency, energy_unit, db_path, overwrite=False)

        assert await _count_prices(db_path) == 2

    async def test_no_price_column_raises(self, tmp_path: Path) -> None:
        csv_path = _write_csv(
            tmp_path,
            "bad.csv",
            "timestamp_from,timestamp_till,amount",
            "2024-01-01T00:00:00+00:00,2024-01-01T00:15:00+00:00,0.25",
        )
        with pytest.raises(ValueError, match="No price column"):
            _read_csv(csv_path)
