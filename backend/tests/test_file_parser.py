"""
Test stubs for user-uploaded file parsing (DATA-13).

DATA-13: Parse CSV, Excel (.xlsx), and JSON files uploaded by users.
Auto-detect column types and surface column mapping for user confirmation.
Implementation target: Plan 07 (file upload + parsing).
"""

import pytest


def test_parse_csv_detects_types():
    """Parsing sample.csv should auto-detect date column and numeric columns."""
    pytest.skip("Wave 0 stub -- implementation in Plan 07")


def test_parse_excel_detects_types():
    """Parsing sample.xlsx should auto-detect the same column types as sample.csv."""
    pytest.skip("Wave 0 stub -- implementation in Plan 07")


def test_parse_json_detects_types():
    """Parsing sample.json (records format) should auto-detect column types."""
    pytest.skip("Wave 0 stub -- implementation in Plan 07")


def test_malformed_csv_autofixes():
    """Parsing malformed.csv should auto-replace non-numeric sentinel values with NaN."""
    pytest.skip("Wave 0 stub -- implementation in Plan 07")
