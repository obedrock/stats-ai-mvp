"""
Test stubs for file upload endpoint (DATA-12, DATA-14).

DATA-12: Accept CSV, Excel, JSON uploads and return parsed preview.
DATA-14: Allow user to override auto-detected column mappings (date, variable names).
Implementation target: Plan 07 (file upload + parsing).
"""

import pytest


def test_upload_csv_returns_preview():
    """Uploading sample.csv should return a JSON preview with detected columns and first 10 rows."""
    pytest.skip("Wave 0 stub -- implementation in Plan 07")


def test_upload_excel_returns_preview():
    """Uploading sample.xlsx should return a JSON preview identical to the CSV upload."""
    pytest.skip("Wave 0 stub -- implementation in Plan 07")


def test_upload_invalid_type_rejected():
    """Uploading a .pdf file should return HTTP 422 with a file-type error message."""
    pytest.skip("Wave 0 stub -- implementation in Plan 07")


def test_mapping_override():
    """User-provided column mapping override should replace auto-detected names in preview."""
    pytest.skip("Wave 0 stub -- implementation in Plan 07")
