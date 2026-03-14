"""Entry point for `python -m leo` and the `leo` console script."""

import structlog

from leo.config import CATEGORIES, Config, SensorConfig, load_config
from leo.exceptions import FetchError, ParseError
from leo.meters import get_power_meter
from leo.prices import get_price_provider

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
    client = get_price_provider(config.energy_provider)
    prices = client.get_future_prices(config.time_resolution)
    log.info(
        "system_check",
        component="provider_client",
        provider=config.energy_provider,
        resolution=config.time_resolution.name,
        prices=len(prices),
        status="ok" if prices else "fail",
    )
    if not prices:
        ok = False

    # Sensor checks
    for category in CATEGORIES:
        sensors: list[SensorConfig] = getattr(config, category)
        for sensor_cfg in sensors:
            try:
                meter = get_power_meter(
                    brand=sensor_cfg.brand,
                    meter_type=sensor_cfg.meter_type,
                    host=sensor_cfg.host,
                    phase=sensor_cfg.phase,
                )
                meter.fetch()
                log.info(
                    "system_check",
                    component="sensor",
                    category=category,
                    host=sensor_cfg.host,
                    type=sensor_cfg.meter_type,
                    status="ok",
                )
            except (FetchError, ParseError) as e:
                log.info(
                    "system_check",
                    component="sensor",
                    category=category,
                    host=sensor_cfg.host,
                    type=sensor_cfg.meter_type,
                    status="fail",
                    error=str(e),
                )
                ok = False

    return ok


def main() -> None:
    config = load_config()
    log.info("config_loaded", provider=config.energy_provider, resolution=config.time_resolution.name)

    if not system_check(config):
        raise SystemExit(1)

    log.info("system_check_passed")


if __name__ == "__main__":
    main()
