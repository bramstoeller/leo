"""Shared logging configuration and CLI arguments."""

import argparse
import logging

import structlog

from leo.console import configure as configure_console


def add_logging_args(parser: argparse.ArgumentParser) -> None:
    """Add --color, --verbose, --debug flags to an argument parser."""
    parser.add_argument(
        "--color",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="enable/disable colored output (default: on)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="enable info logging",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="enable debug + info logging",
    )


def configure_logging(*, verbose: bool, debug: bool, color: bool) -> None:
    """Configure structlog and console output."""
    if debug:
        level = logging.DEBUG
    elif verbose:
        level = logging.INFO
    else:
        level = logging.CRITICAL

    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(level),
        processors=[
            structlog.dev.ConsoleRenderer(colors=color),
        ],
    )
    configure_console(color=color)
