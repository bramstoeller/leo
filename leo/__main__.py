"""Entry point for `python -m leo` and the `leo` console script."""

import asyncio

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


async def _check_provider(config: Config) -> bool:
    client = get_price_provider(config.energy_provider)
    prices = await client.get_future_prices(config.time_resolution)
    log.info(
        "system_check",
        component="provider_client",
        provider=config.energy_provider,
        resolution=config.time_resolution.name,
        prices=len(prices),
        status="ok" if prices else "fail",
    )
    return bool(prices)


async def _check_sensor(category: str, sensor_cfg: SensorConfig) -> bool:
    try:
        meter = get_power_meter(
            brand=sensor_cfg.brand,
            meter_type=sensor_cfg.meter_type,
            host=sensor_cfg.host,
            phase=sensor_cfg.phase,
        )
        await meter.fetch()
        log.info(
            "system_check",
            component="sensor",
            category=category,
            host=sensor_cfg.host,
            type=sensor_cfg.meter_type,
            status="ok",
        )
        return True
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
        return False


async def system_check(config: Config) -> bool:
    """Run system checks for all components in parallel. Returns True if all pass."""
    tasks: list[asyncio.Task[bool]] = []
    tasks.append(asyncio.create_task(_check_provider(config)))

    for category in CATEGORIES:
        sensors: list[SensorConfig] = getattr(config, category)
        for sensor_cfg in sensors:
            tasks.append(asyncio.create_task(_check_sensor(category, sensor_cfg)))

    results = await asyncio.gather(*tasks)
    return all(results)


async def async_main() -> None:
    config = load_config()
    log.info("config_loaded", provider=config.energy_provider, resolution=config.time_resolution.name)

    if not await system_check(config):
        raise SystemExit(1)

    log.info("system_check_passed")


def main() -> None:
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
