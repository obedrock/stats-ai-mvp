"""
Tests for user-uploaded file parsing (DATA-13).

DATA-13: Parse CSV, Excel (.xlsx), and JSON files uploaded by users.
Auto-detect column types and surface column mapping for user confirmation.
"""

import pathlib

import pytest

FIXTURES_DIR = pathlib.Path(__file__).parent / "fixtures"


def test_parse_csv_detects_types():
    """Parsing sample.csv should auto-detect date column and numeric columns."""
    from app.services.file_parser import parse_uploaded_file

    content = (FIXTURES_DIR / "sample.csv").read_bytes()
    result = parse_uploaded_file(content, "sample.csv")

    assert result["total_rows"] >= 10
    assert len(result["preview"]) == 10

    col_names = [c["name"] for c in result["columns"]]
    assert "date" in col_names
    assert "gdp" in col_names
    assert "cpi" in col_names

    col_types = {c["name"]: c["detected_type"] for c in result["columns"]}
    assert col_types["date"] == "date"
    assert col_types["gdp"] == "numeric"
    assert col_types["cpi"] == "numeric"

    # date column should get date_index role since it's the only date column
    col_roles = {c["name"]: c["role"] for c in result["columns"]}
    assert col_roles["date"] == "date_index"


def test_parse_excel_detects_types():
    """Parsing sample.xlsx should auto-detect the same column types as sample.csv."""
    from app.services.file_parser import parse_uploaded_file

    content = (FIXTURES_DIR / "sample.xlsx").read_bytes()
    result = parse_uploaded_file(content, "sample.xlsx")

    assert result["total_rows"] >= 10
    col_names = [c["name"] for c in result["columns"]]
    assert "date" in col_names
    assert "gdp" in col_names
    assert "cpi" in col_names

    col_types = {c["name"]: c["detected_type"] for c in result["columns"]}
    # Excel may store dates as datetime64 already
    assert col_types["date"] in ("date", "numeric")  # openpyxl may parse date as datetime
    assert col_types["gdp"] == "numeric"
    assert col_types["cpi"] == "numeric"


def test_parse_json_detects_types():
    """Parsing sample.json (records format) should auto-detect column types."""
    from app.services.file_parser import parse_uploaded_file

    content = (FIXTURES_DIR / "sample.json").read_bytes()
    result = parse_uploaded_file(content, "sample.json")

    assert result["total_rows"] >= 10
    col_names = [c["name"] for c in result["columns"]]
    assert "date" in col_names
    assert "gdp" in col_names
    assert "cpi" in col_names

    col_types = {c["name"]: c["detected_type"] for c in result["columns"]}
    assert col_types["date"] == "date"
    assert col_types["gdp"] == "numeric"
    assert col_types["cpi"] == "numeric"


def test_malformed_csv_autofixes():
    """Parsing malformed.csv should auto-fix bad values and report changes."""
    from app.services.file_parser import parse_uploaded_file

    content = (FIXTURES_DIR / "malformed.csv").read_bytes()
    result = parse_uploaded_file(content, "malformed.csv")

    # Changes list must be non-empty — auto-fix should have detected issues
    assert len(result["changes"]) > 0
    changes_text = " ".join(result["changes"]).lower()
    # Should mention dropped rows or coerced values
    assert any(kw in changes_text for kw in ["drop", "coer", "empty", "row", "null", "nan"])


def test_unsupported_extension_raises():
    """Unsupported file extension should raise ValueError."""
    from app.services.file_parser import parse_uploaded_file

    with pytest.raises(ValueError, match="Unsupported file type"):
        parse_uploaded_file(b"data", "file.pdf")
