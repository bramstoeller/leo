"""System checks for all configured components."""

import asyncio

import structlog

from leo.config import Config, SensorConfig
from leo.console import pcheck
from leo.exceptions import FetchError, ParseError
from leo.prices import get_price_provider
from leo.sensors import get_power_meter

log = structlog.get_logger()


async def _check_provider(config: Config) -> bool:
    error = None
    try:
        client = get_price_provider(config.price_provider.provider)
        prices = await client.get_future_prices(config.price_provider.time_resolution)
        ok = bool(prices)
    except (FetchError, ParseError) as e:
        prices = []
        ok, error = False, str(e)

    pcheck(str(config.price_provider), ok, msg=error)
    pp = config.price_provider
    if ok:
        log.info("system_check_provider", **(pp.model_dump()), prices=len(prices), status="ok")
    else:
        log.error("system_check_provider", **(pp.model_dump()), status="fail", error=error)
    return ok


async def _check_sensor(category: str, sensor_cfg: SensorConfig) -> bool:
    error = None
    try:
        meter = get_power_meter(**sensor_cfg.model_dump())
        sensor_id = await meter.sensor_id()
        ok = True
    except (FetchError, ParseError) as e:
        sensor_id = None
        ok, error = False, str(e)

    pcheck(str(sensor_cfg), ok, msg=error)
    if ok:
        log.info("system_check_sensor", category=category, sensor_id=sensor_id, **sensor_cfg.model_dump(), status="ok")
    else:
        log.error("system_check_sensor", category=category, **sensor_cfg.model_dump(), status="fail", error=error)

    return ok


async def system_check(config: Config) -> bool:
    """Run system checks for all components in parallel. Returns True if all pass."""
    tasks: list[asyncio.Task[bool]] = []
    tasks.append(asyncio.create_task(_check_provider(config)))

    sensors = {
        "nett_consumption": [config.sensors.nett_consumption],
        "production": config.sensors.production,
        "storage": config.sensors.storage,
    }

    for category, sensor_list in sensors.items():
        for sensor_cfg in sensor_list:
            tasks.append(asyncio.create_task(_check_sensor(category, sensor_cfg)))

    results = await asyncio.gather(*tasks)
    return all(results)
