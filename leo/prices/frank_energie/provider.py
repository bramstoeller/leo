from datetime import date, timedelta
from typing import Any

import requests
from pydantic import AwareDatetime

from leo.exceptions import FetchError
from leo.models.electrical import EnergyUnit
from leo.models.price import Currency, EnergyPrice, EnergyPriceSlot
from leo.models.temporal import TimeResolution
from leo.prices.frank_energie.models import GraphQLResponse
from leo.prices.provider import PriceProvider

_API_ENDPOINT = "https://graphql.frankenergie.nl/"

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


class FrankEnergieProvider(PriceProvider):
    _session: requests.Session | None = None

    def _get_session(self) -> requests.Session:
        if self._session is None:
            self._session = requests.Session()
            self._session.headers.update(
                {
                    "Content-Type": "application/json",
                    "x-graphql-client-name": "frank-app",
                    "x-graphql-client-version": "4.13.3",
                }
            )
        return self._session

    def get_prices(
        self,
        timestamp_from: AwareDatetime,
        timestamp_till: AwareDatetime | None,
        time_resolution: TimeResolution,
    ) -> list[EnergyPriceSlot]:
        # assert timestamps are timezone-aware
        if timestamp_from.tzinfo is None:
            raise ValueError("timestamp_from must be timezone-aware")

        if timestamp_till is not None and timestamp_till.tzinfo is None:
            raise ValueError("timestamp_till must be timezone-aware")

        def in_range(slot: EnergyPriceSlot) -> bool:
            return slot.timestamp_till >= timestamp_from and (
                timestamp_till is None or slot.timestamp_from <= timestamp_till
            )

        prices: list[EnergyPriceSlot] = []

        day = timestamp_from.date()
        while timestamp_till is None or day <= timestamp_till.date():
            try:
                day_prices = self._fetch_day(day, resolution=_TIME_RESOLUTION_MAPPING[time_resolution])
            except FetchError as e:
                if prices and "No marketprices found" in str(e):
                    # No prices for this day, but we already have some prices from previous days, so we can stop here
                    break
                else:
                    raise

            day_prices = [p for p in day_prices if in_range(p)]
            if not day_prices:
                break
            prices += day_prices
            day += timedelta(days=1)

        return sorted(prices, key=lambda p: p.timestamp_from)

    def _fetch_day(self, day: date, resolution: str) -> list[EnergyPriceSlot]:
        data = self._fetch(
            {
                "query": _QUERY,
                "operationName": "MarketPrices",
                "variables": {"date": day.isoformat(), "resolution": resolution},
            }
        )
        return self._parse(data)

    def _fetch(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Send a POST request to the GraphQL endpoint and return the parsed JSON."""
        session = self._get_session()
        resp = session.post(_API_ENDPOINT, json=payload, timeout=15)
        resp.raise_for_status()
        result: dict[str, Any] = resp.json()
        return result

    @staticmethod
    def _parse(data: dict[str, Any]) -> list[EnergyPriceSlot]:
        """Parse a GraphQL response into a list of EnergyPriceSlot objects."""
        response = GraphQLResponse.model_validate(data)

        if response.errors:
            error_str = "; ".join(error.message for error in response.errors)
            raise FetchError(f"GraphQL error: {error_str}")

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
    client = FrankEnergieProvider()
    for price in client.get_future_prices(TimeResolution.QUARTER_HOUR):
        print(price)
