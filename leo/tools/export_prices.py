"""Export all available energy prices to CSV.

Usage: leo_export_prices <provider> <resolution_minutes> <output>
"""

import argparse
import asyncio
import csv
from datetime import datetime
from pathlib import Path

import structlog
from pydantic import AwareDatetime

from leo.console import pheader, pinfo, pval
from leo.exceptions import FetchError
from leo.log import add_logging_args, configure_logging
from leo.models.temporal import TimeResolution
from leo.prices import get_price_provider
from leo.prices.provider import PriceProvider

log = structlog.get_logger()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="leo_export_prices", description="Export energy prices to CSV")
    parser.add_argument("provider", help="price provider name (e.g. frank_energie)")
    parser.add_argument("resolution", type=int, help="time resolution in minutes (e.g. 15 or 60)")
    parser.add_argument("output", type=Path, help="output CSV file path")
    add_logging_args(parser)
    return parser.parse_args()


async def _find_earliest_record(provider: PriceProvider, resolution: TimeResolution) -> AwareDatetime:
    """Binary search for the earliest date with available data."""
    lo = datetime(2000, 1, 1).astimezone()
    hi = datetime.now().astimezone()

    # Assert that there were no prices available at the initial low date, otherwise the binary search would fail
    try:
        await provider.get_prices(timestamp_from=lo, timestamp_till=lo, time_resolution=resolution)
        raise FetchError(f"Expected no prices at {lo.isoformat()}, but got some")
    except FetchError:
        pass

    # Assert that there are prices available at the initial high date, otherwise the binary search would fail
    await provider.get_prices(timestamp_from=hi, timestamp_till=hi, time_resolution=resolution)

    while (hi - lo) > resolution.slot_duration():
        mid = lo + (hi - lo) // 2
        log.debug("binary_search", timestamp=mid.isoformat())
        prices = await provider.get_prices(timestamp_from=mid, timestamp_till=mid, time_resolution=resolution)
        if prices:
            hi = mid
        else:
            lo = mid

    # Find the first available record
    prices = await provider.get_prices(timestamp_from=lo, timestamp_till=hi, time_resolution=resolution)
    return prices[0].timestamp_from


def _write_csv(output: Path, rows: list[list[str]]) -> None:
    with open(output, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp_from", "timestamp_till", "price"])
        writer.writerows(rows)


async def _export_prices(
    provider: PriceProvider, resolution: TimeResolution, earliest: AwareDatetime, output: Path
) -> int:
    prices = await provider.get_prices(
        timestamp_from=earliest,
        timestamp_till=None,
        time_resolution=resolution,
    )

    rows = [
        [
            slot.timestamp_from.isoformat(),
            (slot.timestamp_from + resolution.slot_duration()).isoformat(),
            f"{slot.price.amount:.4f}",
        ]
        for slot in prices
    ]

    await asyncio.to_thread(_write_csv, output, rows)
    return len(rows)


async def _run(args: argparse.Namespace) -> None:
    resolution = TimeResolution(args.resolution)
    provider = get_price_provider(args.provider)

    pheader("LEO - Export Prices")
    pval("Provider", args.provider)
    pval("Resolution", f"{resolution.value} min")
    pval("Output", str(args.output))

    pinfo("Searching for earliest available date...")
    earliest = await _find_earliest_record(provider, resolution)
    pval("Earliest date", earliest.isoformat())

    pinfo("Exporting prices...")
    total = await _export_prices(provider, resolution, earliest, args.output)
    pval("Exported records", str(total))


def main() -> None:
    args = _parse_args()
    configure_logging(verbose=args.verbose, debug=args.debug, color=args.color)
    asyncio.run(_run(args))


if __name__ == "__main__":
    main()
