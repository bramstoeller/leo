"""Tests for the Frank Energie provider client."""

from datetime import UTC, datetime

import pytest

from leo.models.electrical import EnergyUnit
from leo.models.price import Currency
from leo.models.temporal import TimeResolution
from leo.prices.frank_energie.provider import FrankEnergieProvider


def _api_response(prices: list[dict[str, object]]) -> dict[str, object]:
    return {"data": {"marketPrices": {"electricityPrices": prices}}}


def _entry(from_: str, till: str, all_in: float) -> dict[str, object]:
    return {"from": from_, "till": till, "allInPrice": all_in}


SAMPLE = [
    _entry("2026-03-13T10:00:00Z", "2026-03-13T10:15:00Z", 0.15),
    _entry("2026-03-13T10:15:00Z", "2026-03-13T10:30:00Z", 0.18),
]


@pytest.fixture()
def client() -> FrankEnergieProvider:
    return FrankEnergieProvider()


class TestParsePrices:
    def test_parses_entries(self) -> None:
        result = FrankEnergieProvider._parse(_api_response(SAMPLE))

        assert len(result) == 2
        assert result[0].price.amount == 0.15
        assert result[0].price.currency == Currency.EUR
        assert result[0].price.energy_unit == EnergyUnit.KWH
        assert result[0].timestamp_from == datetime(2026, 3, 13, 10, 0, tzinfo=UTC)

    def test_empty_data(self) -> None:
        assert FrankEnergieProvider._parse({"data": None}) == []

    def test_unexpected_structure_raises(self) -> None:
        with pytest.raises(Exception):  # noqa: B017
            FrankEnergieProvider._parse({"data": {"marketPrices": {}}})


class TestGetPrices:
    async def test_filters_by_time_range(self, client: FrankEnergieProvider) -> None:
        entries = [
            _entry("2026-03-13T09:00:00Z", "2026-03-13T09:15:00Z", 0.10),
            _entry("2026-03-13T10:00:00Z", "2026-03-13T10:15:00Z", 0.15),
            _entry("2026-03-13T11:00:00Z", "2026-03-13T11:15:00Z", 0.20),
        ]

        async def mock_fetch_day(day, resolution):  # type: ignore[no-untyped-def]
            return FrankEnergieProvider._parse(_api_response(entries))

        client._fetch_day = mock_fetch_day  # type: ignore[method-assign]

        result = await client.get_prices(
            timestamp_from=datetime(2026, 3, 13, 10, 0, tzinfo=UTC),
            timestamp_till=datetime(2026, 3, 13, 10, 15, tzinfo=UTC),
            time_resolution=TimeResolution.QUARTER_HOUR,
        )

        assert len(result) == 1
        assert result[0].price.amount == 0.15

    async def test_stops_on_empty_day(self, client: FrankEnergieProvider) -> None:
        day1_prices = FrankEnergieProvider._parse(_api_response(SAMPLE))
        responses = iter([day1_prices, []])

        async def mock_fetch_day(day, resolution):  # type: ignore[no-untyped-def]
            return next(responses)

        client._fetch_day = mock_fetch_day  # type: ignore[method-assign]

        result = await client.get_prices(
            timestamp_from=datetime(2026, 3, 13, 9, 0, tzinfo=UTC),
            timestamp_till=None,
            time_resolution=TimeResolution.QUARTER_HOUR,
        )

        assert len(result) == 2


class TestGetFuturePrices:
    async def test_calls_get_prices_from_now(self, client: FrankEnergieProvider) -> None:
        day1_prices = FrankEnergieProvider._parse(
            _api_response([_entry("2099-01-01T12:00:00Z", "2099-01-01T12:15:00Z", 0.15)])
        )
        responses = iter([day1_prices, []])

        async def mock_fetch_day(day, resolution):  # type: ignore[no-untyped-def]
            return next(responses)

        client._fetch_day = mock_fetch_day  # type: ignore[method-assign]

        result = await client.get_future_prices(TimeResolution.QUARTER_HOUR)

        assert len(result) == 1
