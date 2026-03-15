"""Entry point for `python -m leo` and the `leo` console script."""

import argparse
import asyncio
from pathlib import Path

from leo import __version__
from leo.config import DEFAULT_CONFIG_PATH, load_config
from leo.console import perror, pheader, pval
from leo.log import add_logging_args, configure_logging
from leo.system_check import system_check


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="leo", description="Local Energy Optimizer")
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help=f"path to config file (default: {DEFAULT_CONFIG_PATH})",
    )
    add_logging_args(parser)
    return parser.parse_args()


async def _run(args: argparse.Namespace) -> None:
    pheader(f"LEO {__version__}", subtitle="Local Energy Optimizer")

    config = load_config(args.config)
    pval("Config", str(args.config))
    pval("Price provider", str(config.price_provider))
    pval("Time resolution", config.price_provider.time_resolution.name)

    if not await system_check(config):
        perror("System check failed.")
        raise SystemExit(1)


def main() -> None:
    args = _parse_args()
    configure_logging(verbose=args.verbose, debug=args.debug, color=args.color)
    asyncio.run(_run(args))


if __name__ == "__main__":
    main()
