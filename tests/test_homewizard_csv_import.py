"""Tests for HomeWizard CSV import."""

from pathlib import Path

import pytest

from leo.models.electrical import EnergyUnit
from leo.sensors.homewizard.csv_import import import_csv

CSV_HEADER = "time,Import T1 kWh,Import T2 kWh,Export T1 kWh,Export T2 kWh,L1 max W,L2 max W,L3 max W"


def _write_csv(tmp_path: Path, *rows: str) -> Path:
    path = tmp_path / "export.csv"
    path.write_text("\n".join(rows) + "\n")
    return path


def test_basic_import(tmp_path: Path) -> None:
    path = _write_csv(
        tmp_path,
        CSV_HEADER,
        "2024-01-01 00:00,100.000,200.000,50.000,30.000,0,0,0",
        "2024-01-01 00:15,100.500,200.100,50.200,30.050,1200,800,600",
        "2024-01-01 00:30,101.200,200.300,50.600,30.100,1100,900,500",
    )
    slots = import_csv(path, sensor_id="HW-001")

    assert len(slots) == 2

    s0 = slots[0]
    assert s0.sensor_id == "HW-001"
    assert s0.import_total.unit == EnergyUnit.KWH
    assert s0.import_total.value == pytest.approx(0.6)  # 0.5 + 0.1
    assert s0.export_total.value == pytest.approx(0.25)  # 0.2 + 0.05
    assert s0.import_l1 is None
    assert s0.timestamp_from.minute == 0
    assert s0.timestamp_till.minute == 15

    s1 = slots[1]
    assert s1.import_total.value == pytest.approx(0.9)  # 0.7 + 0.2
    assert s1.export_total.value == pytest.approx(0.45)  # 0.4 + 0.05


def test_missing_columns(tmp_path: Path) -> None:
    path = _write_csv(
        tmp_path,
        "time,Import T1 kWh",
        "2024-01-01 00:00,100.000",
    )
    with pytest.raises(ValueError, match="missing required columns"):
        import_csv(path, sensor_id="HW-001")


def test_single_row_raises(tmp_path: Path) -> None:
    path = _write_csv(
        tmp_path,
        CSV_HEADER,
        "2024-01-01 00:00,100.000,200.000,50.000,30.000,0,0,0",
    )
    with pytest.raises(ValueError, match="at least 2 rows"):
        import_csv(path, sensor_id="HW-001")


def test_empty_file(tmp_path: Path) -> None:
    path = _write_csv(tmp_path, "")
    with pytest.raises(ValueError):
        import_csv(path, sensor_id="HW-001")


def test_no_optional_columns(tmp_path: Path) -> None:
    header = "time,Import T1 kWh,Import T2 kWh,Export T1 kWh,Export T2 kWh"
    path = _write_csv(
        tmp_path,
        header,
        "2024-01-01 00:00,100.000,200.000,50.000,30.000",
        "2024-01-01 00:15,100.100,200.050,50.030,30.010",
    )
    slots = import_csv(path, sensor_id="HW-001")
    assert len(slots) == 1
    assert slots[0].import_total.value == pytest.approx(0.15)
    assert slots[0].export_total.value == pytest.approx(0.04)


def test_daily_format(tmp_path: Path) -> None:
    path = _write_csv(
        tmp_path,
        CSV_HEADER,
        "2024-01-01,100.000,200.000,50.000,30.000,0,0,0",
        "2024-01-02,110.000,205.000,55.000,32.000,0,0,0",
    )
    slots = import_csv(path, sensor_id="HW-001")
    assert len(slots) == 1
    assert slots[0].import_total.value == pytest.approx(15.0)
    assert slots[0].export_total.value == pytest.approx(7.0)


def test_bom_encoding(tmp_path: Path) -> None:
    """HomeWizard CSVs may have a UTF-8 BOM."""
    path = tmp_path / "export.csv"
    content = "\n".join(
        [
            CSV_HEADER,
            "2024-01-01 00:00,100.000,200.000,50.000,30.000,0,0,0",
            "2024-01-01 00:15,100.100,200.000,50.000,30.000,0,0,0",
        ]
    )
    path.write_bytes(b"\xef\xbb\xbf" + content.encode("utf-8"))
    slots = import_csv(path, sensor_id="HW-001")
    assert len(slots) == 1
    assert slots[0].import_total.value == pytest.approx(0.1)
