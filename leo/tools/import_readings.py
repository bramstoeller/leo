"""Import energy readings from a HomeWizard CSV into the database.

Usage: leo_import_readings <sensor_id> <csv_file> <database>
"""

import argparse
import asyncio
from pathlib import Path

import structlog

from leo.console import pheader, pinfo, pval
from leo.db import connect
from leo.log import add_logging_args, configure_logging
from leo.sensors.homewizard.csv_import import import_csv

log = structlog.get_logger()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="leo_import_readings", description="Import energy readings from HomeWizard CSV into the database"
    )
    parser.add_argument("sensor_id", help="sensor identifier (e.g. serial number)")
    parser.add_argument("csv_file", type=Path, help="HomeWizard CSV file to import")
    parser.add_argument("database", type=Path, help="SQLite database file")
    add_logging_args(parser)
    return parser.parse_args()


async def _import_readings(sensor_id: str, csv_file: Path, database: Path) -> int:
    slots = await asyncio.to_thread(import_csv, csv_file, sensor_id)

    db = await connect(database)
    try:
        await db.executemany(
            """
            INSERT OR REPLACE INTO energy_readings
                (sensor_id, timestamp_from, timestamp_till,
                 import_total, import_l1, import_l2, import_l3,
                 export_total, export_l1, export_l2, export_l3, unit)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    slot.sensor_id,
                    slot.timestamp_from.isoformat(),
                    slot.timestamp_till.isoformat(),
                    slot.import_total.value,
                    slot.import_l1.value if slot.import_l1 else None,
                    slot.import_l2.value if slot.import_l2 else None,
                    slot.import_l3.value if slot.import_l3 else None,
                    slot.export_total.value,
                    slot.export_l1.value if slot.export_l1 else None,
                    slot.export_l2.value if slot.export_l2 else None,
                    slot.export_l3.value if slot.export_l3 else None,
                    str(slot.import_total.unit),
                )
                for slot in slots
            ],
        )
        await db.commit()
    finally:
        await db.close()
    return len(slots)


async def _run(args: argparse.Namespace) -> None:
    pheader("LEO - Import Readings")
    pval("Sensor ID", args.sensor_id)
    pval("CSV file", str(args.csv_file))
    pval("Database", str(args.database))

    pinfo("Importing readings...")
    total = await _import_readings(args.sensor_id, args.csv_file, args.database)
    pval("Imported records", str(total))


def main() -> None:
    args = _parse_args()
    configure_logging(verbose=args.verbose, debug=args.debug, color=args.color)
    asyncio.run(_run(args))


if __name__ == "__main__":
    main()
