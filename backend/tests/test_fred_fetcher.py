"""
Test stubs for FRED data fetcher (DATA-03).

DATA-03: Fetch macroeconomic series from FRED via fredapi.
Implementation target: Plan 03 (series mapper + FRED fetcher).
"""

import pytest


def test_validate_series_valid_id():
    """Valid FRED series ID (e.g. 'GDP') should pass validation."""
    pytest.skip("Wave 0 stub -- implementation in Plan 03")


def test_validate_series_invalid_returns_suggestions():
    """Invalid FRED series ID should return error with candidate suggestions."""
    pytest.skip("Wave 0 stub -- implementation in Plan 03")


def test_fetch_fred_series_returns_dataframe():
    """Fetching a valid FRED series should return a pandas DataFrame with date index."""
    pytest.skip("Wave 0 stub -- implementation in Plan 03")
