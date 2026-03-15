"""Convert HomeWizard CSV exports to standardized energy readings CSV.

Supports two HomeWizard formats:

P1 meter:
    time,Import T1 kWh,Import T2 kWh,Export T1 kWh,Export T2 kWh[,L1 max W,L2 max W,L3 max W]

kWh meter:
    time,Import kWh,Export kWh[,L1 max W,L2 max W,L3 max W]

Values are cumulative meter readings. This tool computes the delta between
consecutive rows and writes a standardized CSV:

    timestamp_from,timestamp_till,import_kwh,export_kwh

Rows with empty meter values are skipped.

Usage: leo_convert_readings <meter_type> <input_csv> <output_csv>
"""

import argparse
import csv
from datetime import datetime
from itertools import pairwise
from pathlib import Path

from leo.console import pheader, pval
from leo.log import add_logging_args, configure_logging

_TIME = "time"


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


def _has_value(row: dict[str, str], columns: list[str]) -> bool:
    """Check whether all given columns have non-empty values."""
    return all(row[col].strip() != "" for col in columns)


def _read_rows(path: Path, required_columns: set[str]) -> list[dict[str, str]]:
    """Read a CSV file and validate required columns are present."""
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        if reader.fieldnames is None:
            raise ValueError(f"CSV file has no header: {path}")

        missing = required_columns - set(reader.fieldnames)
        if missing:
            raise ValueError(f"CSV missing required columns: {missing}")

        rows = list(reader)

    if len(rows) < 2:
        raise ValueError("CSV needs at least 2 rows to compute deltas")

    return rows


def _convert_p1(input_csv: Path, output_csv: Path) -> int:
    """Convert a HomeWizard P1 meter CSV.

    Columns: time, Import T1 kWh, Import T2 kWh, Export T1 kWh, Export T2 kWh
    T1 and T2 tariffs are summed into a single import/export total.
    """
    import_t1 = "Import T1 kWh"
    import_t2 = "Import T2 kWh"
    export_t1 = "Export T1 kWh"
    export_t2 = "Export T2 kWh"
    value_cols = [import_t1, import_t2, export_t1, export_t2]

    rows = _read_rows(input_csv, {_TIME, *value_cols})

    count = 0
    with open(output_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp_from", "timestamp_till", "import_kwh", "export_kwh"])

        for prev_row, cur_row in pairwise(rows):
            if not _has_value(prev_row, value_cols) or not _has_value(cur_row, value_cols):
                continue

            import_kwh = (
                _parse_float(cur_row[import_t1])
                - _parse_float(prev_row[import_t1])
                + _parse_float(cur_row[import_t2])
                - _parse_float(prev_row[import_t2])
            )
            export_kwh = (
                _parse_float(cur_row[export_t1])
                - _parse_float(prev_row[export_t1])
                + _parse_float(cur_row[export_t2])
                - _parse_float(prev_row[export_t2])
            )

            writer.writerow(
                [
                    _parse_timestamp(prev_row[_TIME]).isoformat(),
                    _parse_timestamp(cur_row[_TIME]).isoformat(),
                    round(import_kwh, 6),
                    round(export_kwh, 6),
                ]
            )
            count += 1

    return count


def _convert_kwh(input_csv: Path, output_csv: Path) -> int:
    """Convert a HomeWizard kWh meter CSV.

    Columns: time, Import kWh, Export kWh
    """
    import_col = "Import kWh"
    export_col = "Export kWh"
    value_cols = [import_col, export_col]

    rows = _read_rows(input_csv, {_TIME, *value_cols})

    count = 0
    with open(output_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp_from", "timestamp_till", "import_kwh", "export_kwh"])

        for prev_row, cur_row in pairwise(rows):
            if not _has_value(prev_row, value_cols) or not _has_value(cur_row, value_cols):
                continue

            import_kwh = _parse_float(cur_row[import_col]) - _parse_float(prev_row[import_col])
            export_kwh = _parse_float(cur_row[export_col]) - _parse_float(prev_row[export_col])

            writer.writerow(
                [
                    _parse_timestamp(prev_row[_TIME]).isoformat(),
                    _parse_timestamp(cur_row[_TIME]).isoformat(),
                    round(import_kwh, 6),
                    round(export_kwh, 6),
                ]
            )
            count += 1

    return count


_CONVERTERS = {"p1": _convert_p1, "kwh": _convert_kwh}


def convert(meter_type: str, input_csv: Path, output_csv: Path) -> int:
    """Convert a HomeWizard CSV to standardized format.

    Returns the number of records written.
    """
    return _CONVERTERS[meter_type](input_csv, output_csv)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="leo_convert_readings",
        description="Convert HomeWizard CSV to standardized energy readings CSV",
    )
    parser.add_argument("meter_type", choices=["p1", "kwh"], help="meter type (p1 or kwh)")
    parser.add_argument("input_csv", type=Path, help="HomeWizard CSV file to convert")
    parser.add_argument("output_csv", type=Path, help="output CSV file path")
    add_logging_args(parser)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    configure_logging(verbose=args.verbose, debug=args.debug, color=args.color)

    pheader("LEO - Convert HomeWizard CSV")
    pval("Meter type", args.meter_type)
    pval("Input", str(args.input_csv))
    pval("Output", str(args.output_csv))

    total = convert(args.meter_type, args.input_csv, args.output_csv)
    pval("Records written", str(total))


if __name__ == "__main__":
    main()
