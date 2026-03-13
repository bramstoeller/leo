"""Entry point for `python -m leo` and the `leo` console script."""

import structlog

from leo.config import Config, load_config
from leo.providers import get_provider_client

structlog.configure(
    processors=[
        structlog.dev.ConsoleRenderer(colors=True),
    ],
)

log = structlog.get_logger()


def system_check(config: Config) -> bool:
    """Run system checks for all components. Returns True if all pass."""
    ok = True

    # Provider client check
    client = get_provider_client(config.energy_provider)
    prices = client.get_future_prices(config.time_resolution)
    minimum = config.time_resolution.slots_per_day()
    log.info(
        "system_check",
        component="provider_client",
        provider=config.energy_provider.value,
        resolution=config.time_resolution.name,
        prices=len(prices),
        minimum=minimum,
        status="ok" if len(prices) >= minimum else "fail",
    )
    if len(prices) < minimum:
        ok = False

    return ok


def main() -> None:
    config = load_config()
    log.info("config loaded", provider=config.energy_provider.value, resolution=config.time_resolution.name)

    if not system_check(config):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
