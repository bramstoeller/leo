"""Human-readable console output that always shows, regardless of log level."""

import textwrap
from enum import StrEnum
from typing import IO, Any

WIDTH = 80
_BORDER = "=" * WIDTH
_RESET = "\033[0m"


class Color(StrEnum):
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"


class Style(StrEnum):
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"


_use_color = False
_sep = " "
_end = "\n"
_file: IO[str] | None = None
_flush = False


def configure(
    *,
    color: bool | None = None,
    sep: str | None = None,
    end: str | None = None,
    file: IO[str] | None = None,
    flush: bool | None = None,
) -> None:
    """Set color and print options for all console functions.

    If an argument is None, the current value is unchanged.

    Args:
        color: Enable or disable colored output.
        sep: Separator between items (default: ' ').
        end: String appended after the last item (default: '\\n').
        file: A file-like object (stream); defaults to the current sys.stdout.
        flush: Whether to forcibly flush the stream after printing (default: False).
    """
    global _use_color, _sep, _end, _file, _flush
    if color is not None:
        _use_color = color
    if sep is not None:
        _sep = sep
    if end is not None:
        _end = end
    if file is not None:
        _file = file
    if flush is not None:
        _flush = flush


def _style(text: str, *codes: Color | Style | str) -> str:
    if not _use_color or not codes:
        return text
    return "".join(codes) + text + _RESET


def _print(*args: str) -> None:
    print(*args, sep=_sep, end=_end, file=_file, flush=_flush)


def pheader(
    title: str,
    *,
    subtitle: str | None = None,
    color: Color = Color.CYAN,
    style: Style = Style.BOLD,
) -> None:
    """Print a prominent startup header."""
    _print(_style(_BORDER, color))
    _print(_style(title.center(WIDTH), style, color))
    if subtitle:
        _print(_style(subtitle.center(WIDTH), Style.DIM, color))
    _print(_style(_BORDER, color))


def pmsg(message: str, *, color: Color | None = None, style: Style | None = None) -> None:
    """Print a message with word wrapping."""
    codes = tuple(c for c in (style, color) if c is not None)
    lines = textwrap.fill(message, width=WIDTH).splitlines()
    for line in lines:
        _print(_style(line, *codes))


def pinfo(message: str) -> None:
    """Print an info message."""
    pmsg(message)


def psuccess(message: str) -> None:
    """Print an info message in green."""
    pmsg(message, color=Color.GREEN)


def pwarning(message: str) -> None:
    """Print a warning message in bold yellow."""
    pmsg(message, color=Color.YELLOW, style=Style.BOLD)


def perror(message: str) -> None:
    """Print an error message in bold red."""
    pmsg(message, color=Color.RED, style=Style.BOLD)


def pval(key: str, value: Any, *, color: Color | None = None, style: Style = Style.BOLD) -> None:
    """Print a key-value pair, left/right aligned with dot fill."""
    dots_len = WIDTH - len(key) - len(str(value)) - 2  # spaces around dots
    if dots_len < 2:
        dots_len = 2
    dots = _style("." * dots_len, Style.DIM)
    value_codes = tuple(c for c in (style, color) if c is not None)
    _print(f"{key} {dots} {_style(str(value), *value_codes)}")


def ppass(name: str, msg: str | None = None) -> None:
    """Print a passing status message in green."""
    pval(name, "OK", color=Color.GREEN)
    if msg:
        psuccess(f" ↳ {msg}")


def pfail(name: str, error: str | None = None) -> None:
    """Print a failing status message in bold red, optionally with an error message."""
    pval(name, "FAIL", color=Color.RED, style=Style.BOLD)
    if error:
        perror(f" ↳ {error}")


def pcheck(name: str, ok: bool, msg: str | None = None) -> None:
    """Print a status message based on the boolean 'ok' value."""
    if ok:
        ppass(name, msg=msg)
    else:
        pfail(name, error=msg)


if __name__ == "__main__":
    configure(color=True)

    pheader("LEO", subtitle="Local Energy Optimizer")

    pval("Price Provider", "frank_energie")
    pval("Time Resolution", "HOURLY")
    pval("Sensors", "3")
    pval("Status", "OK", color=Color.GREEN)

    pinfo("All sensors are reachable and responding with valid data.")
    pwarning("Sensor 'water-heater-1' response time is above 500ms.")
    perror("Failed to connect to sensor 'solar-inverter-2'.")

    pmsg("Running system check...", color=Color.CYAN, style=Style.DIM)

    ppass("homewizard-p1")
    ppass("homewizard-solar")
    pfail("homewizard-water-heater", error="Connection refused (192.168.1.42:80)")
