"""Tests for the price export tool."""

import csv
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from leo.models.electrical import EnergyUnit
from leo.models.price import Currency, EnergyPrice, EnergyPriceSlot
from leo.models.temporal import TimeResolution
from leo.tools.export_prices import _find_earliest_record, _run


def _slot(dt: datetime, price: float) -> EnergyPriceSlot:
    return EnergyPriceSlot(
        timestamp_from=dt,
        timestamp_till=dt + timedelta(minutes=15),
        price=EnergyPrice(amount=price, currency=Currency.EUR, energy_unit=EnergyUnit.KWH),
    )


CUTOFF = datetime(2025, 10, 1, tzinfo=UTC)


class TestFindEarliestRecord:
    async def test_finds_earliest(self) -> None:
        provider = MagicMock()

        async def fake_get_prices(
            timestamp_from: datetime, timestamp_till: datetime | None = None, **kwargs: object
        ) -> list[EnergyPriceSlot]:
            till = timestamp_till or timestamp_from
            if till >= CUTOFF:
                return [_slot(max(timestamp_from, CUTOFF), 0.25)]
            return []

        provider.get_prices = AsyncMock(side_effect=fake_get_prices)

        result = await _find_earliest_record(provider, TimeResolution.QUARTER_HOUR)
        assert result == CUTOFF

    async def test_all_dates_available(self) -> None:
        provider = MagicMock()
        dt = datetime(2020, 1, 1, tzinfo=UTC)
        provider.get_prices = AsyncMock(return_value=[_slot(dt, 0.1)])

        result = await _find_earliest_record(provider, TimeResolution.QUARTER_HOUR)
        assert result == dt


class TestExportPrices:
    @patch("leo.tools.export_prices._find_earliest_record", new_callable=AsyncMock)
    @patch("leo.tools.export_prices.get_price_provider")
    async def test_writes_csv(
        self, mock_get_provider: MagicMock, mock_find_earliest: AsyncMock, tmp_path: Path
    ) -> None:
        earliest = datetime(2026, 3, 14, tzinfo=UTC)
        mock_find_earliest.return_value = earliest

        slots = [
            _slot(datetime(2026, 3, 14, 0, 0, tzinfo=UTC), 0.25),
            _slot(datetime(2026, 3, 14, 0, 15, tzinfo=UTC), 0.30),
        ]

        provider = MagicMock()
        provider.get_prices = AsyncMock(return_value=slots)
        mock_get_provider.return_value = provider

        output = tmp_path / "prices.csv"
        args = MagicMock()
        args.provider = "test_provider"
        args.resolution = 15
        args.output = output

        await _run(args)

        assert output.exists()
        with open(output) as f:
            reader = csv.reader(f)
            header = next(reader)
            assert header == ["timestamp_from", "timestamp_till", "price_eur_kwh"]
            rows = list(reader)

        assert len(rows) == 2
        assert rows[0][0] == "2026-03-14T00:00:00+00:00"
        assert rows[0][1] == "2026-03-14T00:15:00+00:00"
        assert rows[0][2] == "0.2500"
        assert rows[1][0] == "2026-03-14T00:15:00+00:00"
        assert rows[1][1] == "2026-03-14T00:30:00+00:00"
        assert rows[1][2] == "0.3000"
