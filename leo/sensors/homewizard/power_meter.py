from leo.client import AsyncHttpClient
from leo.exceptions import ParseError
from leo.models.electrical import Energy, EnergyUnit, Power
from leo.sensors.homewizard.models import PowerMeterData
from leo.sensors.power_meter import PowerMeter


class HomeWizardPowerMeter(PowerMeter):
    def __init__(self, host: str):
        self._http = AsyncHttpClient()
        self._api_endpoint = f"http://{host}/api/v1/data"
        self._data: PowerMeterData | None = None

    async def close(self) -> None:
        await self._http.close()

    async def fetch(self) -> None:
        response = await self._http.get(self._api_endpoint)
        try:
            self._data = self._parse(response.json())
        except Exception as e:
            raise ParseError(f"Failed to parse response from {self._api_endpoint}") from e

    def _parse(self, data: dict[str, object]) -> PowerMeterData:
        try:
            return PowerMeterData.model_validate(data)
        except Exception as e:
            raise ParseError("Failed to parse power meter data") from e

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
        result: list[Power | None] = [None, None, None]
        result[self.phase - 1] = self._data.active_power_l1
        return result[0], result[1], result[2]


if __name__ == "__main__":
    import asyncio

    async def _main() -> None:
        meter = HomeWizardPowerMeter3Phase("192.168.1.19")
        print(f"Power: {await meter.power()}")
        print(f"Total Import: {await meter.total_import()}")
        print(f"Total Export: {await meter.total_export()}")

    asyncio.run(_main())
