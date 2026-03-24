"""
Test stubs for Yahoo Finance fetcher (DATA-04).

DATA-04: Fetch market data (equities, ETFs, indices) via yfinance.
Implementation target: Plan 04 (Yahoo Finance fetcher).
"""

import pytest


def test_fetch_yahoo_series_returns_dataframe():
    """Fetching a valid ticker (e.g. 'AAPL') should return a pandas DataFrame."""
    pytest.skip("Wave 0 stub -- implementation in Plan 04")


def test_fetch_yahoo_invalid_ticker_raises():
    """Fetching an invalid ticker symbol should raise a descriptive error."""
    pytest.skip("Wave 0 stub -- implementation in Plan 04")
