"""Tests for the Frank Energie provider client."""

from datetime import UTC, datetime
from typing import Any
from unittest.mock import patch

import pytest

from leo.models.energy import EnergyUnit
from leo.models.price import Currency
from leo.models.time import TimeResolution
from leo.providers.frank_energie.client import FrankEnergieClient


def _api_response(prices: list[dict[str, object]]) -> dict[str, object]:
    return {"data": {"marketPrices": {"electricityPrices": prices}}}


def _entry(from_: str, till: str, all_in: float) -> dict[str, object]:
    return {"from": from_, "till": till, "allInPrice": all_in}


SAMPLE = [
    _entry("2026-03-13T10:00:00Z", "2026-03-13T10:15:00Z", 0.15),
    _entry("2026-03-13T10:15:00Z", "2026-03-13T10:30:00Z", 0.18),
]


@pytest.fixture()
def client() -> FrankEnergieClient:
    return FrankEnergieClient(url="https://test.example.com/graphql")


class TestParsePrices:
    def test_parses_entries(self) -> None:
        result = FrankEnergieClient._parse_prices(_api_response(SAMPLE))

        assert len(result) == 2
        assert result[0].price.amount == 0.15
        assert result[0].price.currency == Currency.EUR
        assert result[0].price.energy_unit == EnergyUnit.KWH
        assert result[0].timestamp_from == datetime(2026, 3, 13, 10, 0, tzinfo=UTC)

    def test_empty_data(self) -> None:
        assert FrankEnergieClient._parse_prices({"data": None}) == []
        assert FrankEnergieClient._parse_prices({}) == []

    def test_unexpected_structure_raises(self) -> None:
        with pytest.raises(ValueError, match="Unexpected response format"):
            FrankEnergieClient._parse_prices({"data": {"marketPrices": {}}})


class TestGetPrices:
    def test_filters_by_time_range(self, client: FrankEnergieClient) -> None:
        entries = [
            _entry("2026-03-13T09:00:00Z", "2026-03-13T09:15:00Z", 0.10),
            _entry("2026-03-13T10:00:00Z", "2026-03-13T10:15:00Z", 0.15),
            _entry("2026-03-13T11:00:00Z", "2026-03-13T11:15:00Z", 0.20),
        ]
        client._post = lambda _: _api_response(entries)  # type: ignore[assignment]

        result = client.get_prices(
            timestamp_from=datetime(2026, 3, 13, 10, 0, tzinfo=UTC),
            timestamp_till=datetime(2026, 3, 13, 10, 15, tzinfo=UTC),
            resolution=TimeResolution.QUARTER_HOUR,
        )

        assert len(result) == 1
        assert result[0].price.amount == 0.15

    def test_stops_on_empty_day(self, client: FrankEnergieClient) -> None:
        day1 = _api_response(SAMPLE)
        day2: dict[str, Any] = {"data": None}
        responses = iter([day1, day2])
        client._post = lambda _: next(responses)  # type: ignore[assignment]

        result = client.get_prices(
            timestamp_from=datetime(2026, 3, 13, 9, 0, tzinfo=UTC),
            timestamp_till=None,
            resolution=TimeResolution.QUARTER_HOUR,
        )

        assert len(result) == 2


class TestGetFuturePrices:
    @patch("leo.providers.client.datetime")
    def test_calls_get_prices_from_now(self, mock_dt: Any, client: FrankEnergieClient) -> None:
        now = datetime(2026, 3, 13, 12, 0, tzinfo=UTC)
        mock_dt.now.return_value = now

        day1 = _api_response([_entry("2026-03-13T12:00:00Z", "2026-03-13T12:15:00Z", 0.15)])
        day2: dict[str, Any] = {"data": None}
        responses = iter([day1, day2])
        client._post = lambda _: next(responses)  # type: ignore[assignment]

        result = client.get_future_prices(TimeResolution.QUARTER_HOUR)

        assert len(result) == 1
        mock_dt.now.assert_called_once_with(UTC)
