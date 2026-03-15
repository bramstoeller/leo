"""Import energy prices from CSV into the database.

Usage: leo_import_prices <csv_file> <database>
"""

import argparse
import asyncio
import csv
from pathlib import Path

import structlog

from leo.console import pheader, pinfo, pval
from leo.db import connect
from leo.log import add_logging_args, configure_logging

log = structlog.get_logger()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="leo_import_prices", description="Import energy prices from CSV into the database"
    )
    parser.add_argument("csv_file", type=Path, help="CSV file to import")
    parser.add_argument("database", type=Path, help="SQLite database file")
    add_logging_args(parser)
    return parser.parse_args()


def _read_csv(path: Path) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


async def _import_prices(rows: list[dict[str, str]], database: Path) -> int:
    db = await connect(database)
    try:
        await db.executemany(
            """
            INSERT OR REPLACE INTO energy_prices
                (provider_id, timestamp_from, timestamp_till, amount, currency, energy_unit)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    row.get("provider_id", "unknown"),
                    row["timestamp_from"],
                    row["timestamp_till"],
                    float(row["price"]),
                    row.get("currency", "EUR"),
                    row.get("energy_unit", "kWh"),
                )
                for row in rows
            ],
        )
        await db.commit()
    finally:
        await db.close()
    return len(rows)


async def _run(args: argparse.Namespace) -> None:
    pheader("LEO - Import Prices")
    pval("CSV file", str(args.csv_file))
    pval("Database", str(args.database))

    pinfo("Reading CSV...")
    rows = await asyncio.to_thread(_read_csv, args.csv_file)
    pval("Records in CSV", str(len(rows)))

    pinfo("Importing into database...")
    total = await _import_prices(rows, args.database)
    pval("Imported records", str(total))


def main() -> None:
    args = _parse_args()
    configure_logging(verbose=args.verbose, debug=args.debug, color=args.color)
    asyncio.run(_run(args))


if __name__ == "__main__":
    main()
