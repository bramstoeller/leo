"""Tests for HomeWizard CSV to standardized CSV conversion."""

import csv
from pathlib import Path

import pytest

from leo.tools.convert_homewizard_csv import convert


def _write_csv(tmp_path: Path, *rows: str) -> Path:
    path = tmp_path / "input.csv"
    path.write_text("\n".join(rows) + "\n")
    return path


def _read_output(path: Path) -> list[dict[str, str]]:
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


P1_HEADER = "time,Import T1 kWh,Import T2 kWh,Export T1 kWh,Export T2 kWh,L1 max W,L2 max W,L3 max W"
KWH_HEADER = "time,Import kWh,Export kWh"


class TestConvertP1:
    def test_basic_conversion(self, tmp_path: Path) -> None:
        input_csv = _write_csv(
            tmp_path,
            P1_HEADER,
            "2024-01-01 00:00,100.000,200.000,50.000,30.000,0,0,0",
            "2024-01-01 00:15,100.500,200.100,50.200,30.050,1200,800,600",
            "2024-01-01 00:30,101.200,200.300,50.600,30.100,1100,900,500",
        )
        output_csv = tmp_path / "output.csv"

        total = convert("p1", input_csv, output_csv)

        assert total == 2
        rows = _read_output(output_csv)
        assert len(rows) == 2
        assert set(rows[0].keys()) == {"timestamp_from", "timestamp_till", "import_kwh", "export_kwh"}
        assert float(rows[0]["import_kwh"]) == pytest.approx(0.6)  # 0.5 + 0.1
        assert float(rows[0]["export_kwh"]) == pytest.approx(0.25)  # 0.2 + 0.05
        assert float(rows[1]["import_kwh"]) == pytest.approx(0.9)  # 0.7 + 0.2
        assert float(rows[1]["export_kwh"]) == pytest.approx(0.45)  # 0.4 + 0.05

    def test_missing_columns(self, tmp_path: Path) -> None:
        input_csv = _write_csv(tmp_path, "time,Import T1 kWh", "2024-01-01 00:00,100.000")
        with pytest.raises(ValueError, match="missing required columns"):
            convert("p1", input_csv, tmp_path / "output.csv")

    def test_single_row_raises(self, tmp_path: Path) -> None:
        input_csv = _write_csv(tmp_path, P1_HEADER, "2024-01-01 00:00,100.000,200.000,50.000,30.000,0,0,0")
        with pytest.raises(ValueError, match="at least 2 rows"):
            convert("p1", input_csv, tmp_path / "output.csv")

    def test_no_optional_columns(self, tmp_path: Path) -> None:
        header = "time,Import T1 kWh,Import T2 kWh,Export T1 kWh,Export T2 kWh"
        input_csv = _write_csv(
            tmp_path,
            header,
            "2024-01-01 00:00,100.000,200.000,50.000,30.000",
            "2024-01-01 00:15,100.100,200.050,50.030,30.010",
        )
        output_csv = tmp_path / "output.csv"
        total = convert("p1", input_csv, output_csv)
        assert total == 1
        rows = _read_output(output_csv)
        assert float(rows[0]["import_kwh"]) == pytest.approx(0.15)
        assert float(rows[0]["export_kwh"]) == pytest.approx(0.04)

    def test_daily_format(self, tmp_path: Path) -> None:
        input_csv = _write_csv(
            tmp_path,
            P1_HEADER,
            "2024-01-01,100.000,200.000,50.000,30.000,0,0,0",
            "2024-01-02,110.000,205.000,55.000,32.000,0,0,0",
        )
        output_csv = tmp_path / "output.csv"
        total = convert("p1", input_csv, output_csv)
        assert total == 1
        rows = _read_output(output_csv)
        assert float(rows[0]["import_kwh"]) == pytest.approx(15.0)
        assert float(rows[0]["export_kwh"]) == pytest.approx(7.0)

    def test_bom_encoding(self, tmp_path: Path) -> None:
        """HomeWizard CSVs may have a UTF-8 BOM."""
        path = tmp_path / "input.csv"
        content = "\n".join(
            [
                P1_HEADER,
                "2024-01-01 00:00,100.000,200.000,50.000,30.000,0,0,0",
                "2024-01-01 00:15,100.100,200.000,50.000,30.000,0,0,0",
            ]
        )
        path.write_bytes(b"\xef\xbb\xbf" + content.encode("utf-8"))
        output_csv = tmp_path / "output.csv"
        total = convert("p1", path, output_csv)
        assert total == 1
        rows = _read_output(output_csv)
        assert float(rows[0]["import_kwh"]) == pytest.approx(0.1)

    def test_skips_empty_rows(self, tmp_path: Path) -> None:
        input_csv = _write_csv(
            tmp_path,
            P1_HEADER,
            "2024-01-01 00:00,,,,,,,",
            "2024-01-01 00:15,,,,,,,",
            "2024-01-01 00:30,100.000,200.000,50.000,30.000,0,0,0",
            "2024-01-01 00:45,100.500,200.100,50.200,30.050,0,0,0",
        )
        output_csv = tmp_path / "output.csv"
        total = convert("p1", input_csv, output_csv)
        assert total == 1
        rows = _read_output(output_csv)
        assert float(rows[0]["import_kwh"]) == pytest.approx(0.6)


class TestConvertKwh:
    def test_basic_conversion(self, tmp_path: Path) -> None:
        input_csv = _write_csv(
            tmp_path,
            KWH_HEADER,
            "2024-01-01 00:00,100.000,50.000",
            "2024-01-01 00:15,100.500,50.200",
            "2024-01-01 00:30,101.200,50.600",
        )
        output_csv = tmp_path / "output.csv"

        total = convert("kwh", input_csv, output_csv)

        assert total == 2
        rows = _read_output(output_csv)
        assert len(rows) == 2
        assert float(rows[0]["import_kwh"]) == pytest.approx(0.5)
        assert float(rows[0]["export_kwh"]) == pytest.approx(0.2)
        assert float(rows[1]["import_kwh"]) == pytest.approx(0.7)
        assert float(rows[1]["export_kwh"]) == pytest.approx(0.4)

    def test_missing_columns(self, tmp_path: Path) -> None:
        input_csv = _write_csv(tmp_path, "time,Import kWh", "2024-01-01 00:00,100.000")
        with pytest.raises(ValueError, match="missing required columns"):
            convert("kwh", input_csv, tmp_path / "output.csv")

    def test_single_row_raises(self, tmp_path: Path) -> None:
        input_csv = _write_csv(tmp_path, KWH_HEADER, "2024-01-01 00:00,100.000,50.000")
        with pytest.raises(ValueError, match="at least 2 rows"):
            convert("kwh", input_csv, tmp_path / "output.csv")

    def test_empty_file(self, tmp_path: Path) -> None:
        input_csv = _write_csv(tmp_path, "")
        with pytest.raises(ValueError):
            convert("kwh", input_csv, tmp_path / "output.csv")

    def test_daily_format(self, tmp_path: Path) -> None:
        input_csv = _write_csv(
            tmp_path,
            KWH_HEADER,
            "2024-01-01,100.000,50.000",
            "2024-01-02,110.000,55.000",
        )
        output_csv = tmp_path / "output.csv"
        total = convert("kwh", input_csv, output_csv)
        assert total == 1
        rows = _read_output(output_csv)
        assert float(rows[0]["import_kwh"]) == pytest.approx(10.0)
        assert float(rows[0]["export_kwh"]) == pytest.approx(5.0)

    def test_skips_empty_rows(self, tmp_path: Path) -> None:
        input_csv = _write_csv(
            tmp_path,
            KWH_HEADER,
            "2024-01-01 00:00,,",
            "2024-01-01 00:15,,",
            "2024-01-01 00:30,100.000,50.000",
            "2024-01-01 00:45,100.500,50.200",
        )
        output_csv = tmp_path / "output.csv"
        total = convert("kwh", input_csv, output_csv)
        assert total == 1
        rows = _read_output(output_csv)
        assert float(rows[0]["import_kwh"]) == pytest.approx(0.5)
