"""Entry point for `python -m leo` and the `leo` console script."""

import asyncio

import structlog

from leo.config import CATEGORIES, Config, SensorConfig, load_config
from leo.exceptions import FetchError, ParseError
from leo.prices import get_price_provider
from leo.sensors import get_power_meter

structlog.configure(
    processors=[
        structlog.dev.ConsoleRenderer(colors=True),
    ],
)

log = structlog.get_logger()


async def _check_provider(config: Config) -> bool:
    client = get_price_provider(config.price_provider)
    prices = await client.get_future_prices(config.time_resolution)
    log.info(
        "system_check",
        component="provider_client",
        provider=config.price_provider,
        resolution=config.time_resolution.name,
        prices=len(prices),
        status="ok" if prices else "fail",
    )
    return bool(prices)


async def _check_sensor(category: str, sensor_cfg: SensorConfig) -> bool:
    try:
        meter = get_power_meter(**sensor_cfg.model_dump())
        await meter.fetch()
        log.info(
            "system_check",
            component="sensor",
            category=category,
            **sensor_cfg.model_dump(),
            status="ok",
        )
        return True
    except (FetchError, ParseError) as e:
        log.error(
            "system_check",
            component="sensor",
            category=category,
            **sensor_cfg.model_dump(),
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
    log.info("config_loaded", provider=config.price_provider, resolution=config.time_resolution.name)

    if not await system_check(config):
        raise SystemExit(1)

    log.info("system_check_passed")


def main() -> None:
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
