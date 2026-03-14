from datetime import date, timedelta
from typing import Any

import httpx
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

_HEADERS = {
    "Content-Type": "application/json",
    "x-graphql-client-name": "frank-app",
    "x-graphql-client-version": "4.13.3",
}


class FrankEnergieProvider(PriceProvider):
    _client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(headers=_HEADERS)
        return self._client

    async def get_prices(
        self,
        timestamp_from: AwareDatetime,
        timestamp_till: AwareDatetime | None,
        time_resolution: TimeResolution,
    ) -> list[EnergyPriceSlot]:
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
                day_prices = await self._fetch_day(day, resolution=_TIME_RESOLUTION_MAPPING[time_resolution])
            except FetchError as e:
                if prices and "No marketprices found" in str(e):
                    break
                else:
                    raise

            day_prices = [p for p in day_prices if in_range(p)]
            if not day_prices:
                break
            prices += day_prices
            day += timedelta(days=1)

        return sorted(prices, key=lambda p: p.timestamp_from)

    async def _fetch_day(self, day: date, resolution: str) -> list[EnergyPriceSlot]:
        data = await self._fetch(
            {
                "query": _QUERY,
                "operationName": "MarketPrices",
                "variables": {"date": day.isoformat(), "resolution": resolution},
            }
        )
        return self._parse(data)

    async def _fetch(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Send a POST request to the GraphQL endpoint and return the parsed JSON."""
        client = await self._get_client()
        resp = await client.post(_API_ENDPOINT, json=payload, timeout=15)
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
    import asyncio

    async def _main() -> None:
        client = FrankEnergieProvider()
        for price in await client.get_future_prices(TimeResolution.QUARTER_HOUR):
            print(price)

    asyncio.run(_main())
