from abc import ABC, abstractmethod
from datetime import UTC, datetime

from pydantic import AwareDatetime

from leo.models.price import EnergyPriceSlot
from leo.models.time import TimeResolution


class ProviderClient(ABC):
    """
    Base class for energy provider clients.
    """

    @abstractmethod
    def get_prices(
        self,
        timestamp_from: AwareDatetime,
        timestamp_till: AwareDatetime | None,
        time_resolution: TimeResolution,
    ) -> list[EnergyPriceSlot]:
        """
        Fetch electricity prices from the provider for a specific time range.
        Should return a list of EnergyPriceSlot objects, sorted chronologically.

        Args:
            timestamp_from: Start of the time range for which to fetch prices.
            timestamp_till: End of the time range. If None, fetch from timestamp_from onwards.
            time_resolution: Time resolution for the prices.

        Returns:
            List of EnergyPriceSlot sorted chronologically.
        """
        pass

    def get_future_prices(self, time_resolution: TimeResolution) -> list[EnergyPriceSlot]:
        """
        Fetch all available future electricity prices from the provider.

        Args:
            time_resolution: Time resolution for the prices.
        """
        return self.get_prices(datetime.now(UTC), None, time_resolution)
