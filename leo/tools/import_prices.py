"""Import energy prices from CSV into the database.

Expected CSV format:

    timestamp_from,timestamp_till,price_{currency}_{unit}

The price column name encodes the currency and energy unit, e.g.
price_eur_kwh means EUR per kWh.

Usage: leo_import_prices <provider> <csv_file> <database> [--overwrite]
"""

import argparse
import asyncio
import csv
import re
import sqlite3
import sys
from pathlib import Path

import structlog

from leo.console import perror, pheader, pinfo, pval
from leo.db import connect, get_or_create_provider
from leo.log import add_logging_args, configure_logging

log = structlog.get_logger()

_PRICE_COLUMN_RE = re.compile(r"^price_([a-z]+)_([a-z]+)$")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="leo_import_prices", description="Import energy prices from CSV into the database"
    )
    parser.add_argument("provider", help="provider identifier (e.g. frank_energie)")
    parser.add_argument("csv_file", type=Path, help="CSV file to import")
    parser.add_argument("database", type=Path, help="SQLite database file")
    parser.add_argument("--overwrite", action="store_true", help="overwrite existing records instead of failing")
    add_logging_args(parser)
    return parser.parse_args()


def _find_price_column(columns: list[str]) -> tuple[str, str, str]:
    """Find the price_*_* column and return (column_name, currency, energy_unit)."""
    for col in columns:
        match = _PRICE_COLUMN_RE.match(col)
        if match:
            return col, match.group(1).upper(), match.group(2)
    raise ValueError(f"No price column matching price_{{currency}}_{{unit}} found in: {columns}")


def _read_csv(path: Path) -> tuple[list[dict[str, str]], str, str, str]:
    """Read CSV and detect the price column. Returns (rows, price_column, currency, energy_unit)."""
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError(f"CSV file has no header: {path}")
        price_col, currency, energy_unit = _find_price_column(list(reader.fieldnames))
        rows = list(reader)
    return rows, price_col, currency, energy_unit


async def _import_prices(
    provider: str,
    rows: list[dict[str, str]],
    price_column: str,
    currency: str,
    energy_unit: str,
    database: Path,
    overwrite: bool,
) -> int:
    db = await connect(database)
    try:
        provider_id = await get_or_create_provider(db, provider)
        verb = "INSERT OR REPLACE" if overwrite else "INSERT"
        await db.executemany(
            f"""
            {verb} INTO energy_prices
                (provider_id, timestamp_from, timestamp_till, amount, currency, energy_unit)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    provider_id,
                    row["timestamp_from"],
                    row["timestamp_till"],
                    float(row[price_column]),
                    currency,
                    energy_unit,
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
    pheader("LEO - Import Prices")
    pval("Provider", args.provider)
    pval("CSV file", str(args.csv_file))
    pval("Database", str(args.database))
    pval("Overwrite", str(args.overwrite))

    pinfo("Reading CSV...")
    rows, price_col, currency, energy_unit = await asyncio.to_thread(_read_csv, args.csv_file)
    pval("Records in CSV", str(len(rows)))
    pval("Currency", currency)
    pval("Energy unit", energy_unit)

    pinfo("Importing into database...")
    try:
        total = await _import_prices(
            args.provider, rows, price_col, currency, energy_unit, args.database, args.overwrite
        )
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
