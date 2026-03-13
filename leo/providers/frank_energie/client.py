from datetime import date, timedelta
from typing import Any

import requests
from pydantic import AwareDatetime

from leo.models.energy import EnergyUnit
from leo.models.price import Currency, EnergyPrice, EnergyPriceSlot
from leo.models.temporal import TimeResolution
from leo.providers.client import ProviderClient
from leo.providers.frank_energie.models import GraphQLResponse

_URL = "https://graphql.frankenergie.nl/"

_QUERY = """
query MarketPrices($date: String!, $resolution: PriceResolution!) {
    marketPrices(date: $date, resolution: $resolution) {
        electricityPrices {
            from
            till
            allInPrice
        }
    }
}
"""

_TIME_RESOLUTION_MAPPING = {
    TimeResolution.QUARTER_HOUR: "PT15M",
    TimeResolution.HOURLY: "PT1H",
}


class FrankEnergieClient(ProviderClient):
    """
    Frank Energie client: https://www.frankenergie.nl
    """

    url: str
    session: requests.Session

    def __init__(self, url: str = _URL) -> None:
        super().__init__()
        self.url = url
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "x-graphql-client-name": "frank-app",
                "x-graphql-client-version": "4.13.3",
            }
        )

    def get_prices(
        self,
        timestamp_from: AwareDatetime,
        timestamp_till: AwareDatetime | None,
        resolution: TimeResolution,
    ) -> list[EnergyPriceSlot]:
        prices: list[EnergyPriceSlot] = []

        day = timestamp_from.astimezone().date()
        while timestamp_till is None or day <= timestamp_till.astimezone().date():
            day_prices = self._fetch_day(day, resolution=_TIME_RESOLUTION_MAPPING[resolution])
            day_prices = [
                p
                for p in day_prices
                if p.timestamp_till >= timestamp_from and (timestamp_till is None or p.timestamp_from <= timestamp_till)
            ]
            if not day_prices:
                break
            prices += day_prices
            day += timedelta(days=1)

        return sorted(prices, key=lambda p: p.timestamp_from)

    def _fetch_day(self, day: date, resolution: str) -> list[EnergyPriceSlot]:
        data = self._post(
            {
                "query": _QUERY,
                "operationName": "MarketPrices",
                "variables": {"date": day.isoformat(), "resolution": resolution},
            }
        )
        return self._parse_prices(data)

    def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Send a POST request to the GraphQL endpoint and return the parsed JSON."""
        resp = self.session.post(self.url, json=payload, timeout=15)
        resp.raise_for_status()
        result: dict[str, Any] = resp.json()
        return result

    @staticmethod
    def _parse_prices(data: dict[str, Any]) -> list[EnergyPriceSlot]:
        """Parse a GraphQL response into a list of EnergyPriceSlot objects."""
        response = GraphQLResponse.model_validate(data)
        if response.data is None:
            return []

        return [
            EnergyPriceSlot(
                timestamp_from=entry.price_from,
                timestamp_till=entry.price_till,
                price=EnergyPrice(amount=entry.all_in_price, currency=Currency.EUR, energy_unit=EnergyUnit.KWH),
            )
            for entry in response.data.market_prices.electricity_prices
        ]


if __name__ == "__main__":
    client = FrankEnergieClient()
    for price in client.get_future_prices(TimeResolution.QUARTER_HOUR):
        print(price)
