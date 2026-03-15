"""Import energy readings from a standardized CSV into the database.

Expected CSV format:

    timestamp_from,timestamp_till,import_kwh,export_kwh

Usage: leo_import_readings <sensor_uid> <csv_file> <database> [--overwrite]
"""

import argparse
import asyncio
import csv
import sqlite3
import sys
from pathlib import Path

import structlog

from leo.console import perror, pheader, pinfo, pval
from leo.db import connect, get_or_create_sensor
from leo.log import add_logging_args, configure_logging
from leo.models.electrical import Energy, EnergyUnit

log = structlog.get_logger()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="leo_import_readings", description="Import energy readings from standardized CSV into the database"
    )
    parser.add_argument("sensor_uid", help="sensor identifier (e.g. homewizard.<serial>)")
    parser.add_argument("csv_file", type=Path, help="standardized CSV file to import")
    parser.add_argument("database", type=Path, help="SQLite database file")
    parser.add_argument("--overwrite", action="store_true", help="overwrite existing records instead of failing")
    add_logging_args(parser)
    return parser.parse_args()


def _read_csv(path: Path) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


async def _import_readings(sensor_uid: str, rows: list[dict[str, str]], database: Path, overwrite: bool) -> int:
    db = await connect(database)
    try:
        sensor_id = await get_or_create_sensor(db, sensor_uid)
        verb = "INSERT OR REPLACE" if overwrite else "INSERT"
        await db.executemany(
            f"""
            {verb} INTO energy_readings
                (sensor_id, timestamp_from, timestamp_till,
                 import_total, export_total, unit)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    sensor_id,
                    row["timestamp_from"],
                    row["timestamp_till"],
                    Energy(value=float(row["import_kwh"]), unit=EnergyUnit.KWH).to(EnergyUnit.J).value,
                    Energy(value=float(row["export_kwh"]), unit=EnergyUnit.KWH).to(EnergyUnit.J).value,
                    str(EnergyUnit.J),
                )
                for row in rows
            ],
        )
        await db.commit()
    except sqlite3.IntegrityError:
        await db.rollback()
        raise
    except Exception:
        await db.rollback()
        raise
    finally:
        await db.close()
    return len(rows)


async def _run(args: argparse.Namespace) -> None:
    pheader("LEO - Import Readings")
    pval("Sensor", args.sensor_uid)
    pval("CSV file", str(args.csv_file))
    pval("Database", str(args.database))
    pval("Overwrite", str(args.overwrite))

    pinfo("Reading CSV...")
    rows = await asyncio.to_thread(_read_csv, args.csv_file)
    pval("Records in CSV", str(len(rows)))

    pinfo("Importing into database...")
    try:
        total = await _import_readings(args.sensor_uid, rows, args.database, args.overwrite)
    except sqlite3.IntegrityError:
        perror("Import failed: duplicate records found. Use --overwrite to replace existing data.")
        sys.exit(1)
    pval("Imported records", str(total))


def main() -> None:
    args = _parse_args()
    configure_logging(verbose=args.verbose, debug=args.debug, color=args.color)
    asyncio.run(_run(args))


if __name__ == "__main__":
    main()
