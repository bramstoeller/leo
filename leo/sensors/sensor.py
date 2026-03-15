from abc import ABC, abstractmethod


class Sensor(ABC):
    _sensor_id: str | None = None

    @abstractmethod
    async def _get_unique_id(self) -> str:
        pass

    async def sensor_id(self) -> str:
        if self._sensor_id is None:
            self._sensor_id = await self._get_unique_id()
        return f"{type(self).__name__}.{self._sensor_id}"
