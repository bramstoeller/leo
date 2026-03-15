import structlog

from leo.client import AsyncHttpClient
from leo.exceptions import ParseError
from leo.models.electrical import Energy, EnergyUnit, Power, PowerUnit
from leo.sensors.homewizard.models import DeviceInfo, PowerMeterData
from leo.sensors.power_meter import PowerMeter

log = structlog.get_logger()


class HomeWizardPowerMeter(PowerMeter):
    def __init__(self, host: str):
        self._http = AsyncHttpClient()
        self._host_url = f"http://{host}"
        self._data: PowerMeterData | None = None
        log.debug("homewizard_init", host=host)

    async def close(self) -> None:
        await self._http.close()
        log.debug("homewizard_closed", host=self._host_url)

    async def _get_unique_id(self) -> str:
        url = f"{self._host_url}/api"
        response = await self._http.get(url)
        try:
            info = DeviceInfo.model_validate(response.json())
        except Exception as e:
            raise ParseError(f"Failed to parse device info from {url}") from e
        log.debug("homewizard_device_info", host=self._host_url, **info.model_dump())
        return info.serial_number

    async def fetch(self) -> None:
        url = f"{self._host_url}/api/v1/data"
        response = await self._http.get(url)
        try:
            self._data = PowerMeterData.model_validate(response.json())
        except Exception as e:
            raise ParseError(f"Failed to parse response from {url}") from e
        log.debug("homewizard_fetch", host=self._host_url, **self._data.model_dump())

    async def total_import(self, fetch: bool = True) -> Energy | None:
        if fetch:
            await self.fetch()
        if self._data is None or self._data.total_power_import_kwh is None:
            return None
        return Energy(value=self._data.total_power_import_kwh, unit=EnergyUnit.KWH)

    async def total_export(self, fetch: bool = True) -> Energy | None:
        if fetch:
            await self.fetch()
        if self._data is None or self._data.total_power_export_kwh is None:
            return None
        return Energy(value=self._data.total_power_export_kwh, unit=EnergyUnit.KWH)


class HomeWizardPowerMeter3Phase(HomeWizardPowerMeter):
    async def power(self, fetch: bool = True) -> tuple[Power | None, Power | None, Power | None]:
        if fetch:
            await self.fetch()
        if self._data is None:
            return None, None, None
        return self._data.active_power_l1, self._data.active_power_l2, self._data.active_power_l3


class HomeWizardPowerMeter1Phase(HomeWizardPowerMeter):
    def __init__(self, host: str, phase: int):
        super().__init__(host)
        if phase not in (1, 2, 3):
            raise ValueError("Phase must be 1, 2, or 3")
        self.phase = phase

    async def power(self, fetch: bool = True) -> tuple[Power | None, Power | None, Power | None]:
        if fetch:
            await self.fetch()
        if self._data is None:
            return None, None, None
        zero = Power(value=0, unit=PowerUnit.W)
        result: list[Power] = [zero, zero, zero]
        result[self.phase - 1] = self._data.active_power_l1 or zero
        return result[0], result[1], result[2]


if __name__ == "__main__":
    import asyncio

    async def _main() -> None:
        meter = HomeWizardPowerMeter3Phase("192.168.1.19")
        print(f"Power: {await meter.power()}")
        print(f"Total Import: {await meter.total_import()}")
        print(f"Total Export: {await meter.total_export()}")

    asyncio.run(_main())
