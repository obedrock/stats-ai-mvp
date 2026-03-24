"""Tests for yahoo_fetcher.py — Yahoo Finance data fetching."""
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from app.services import yahoo_fetcher


def test_fetch_yahoo_series_returns_dataframe():
    """fetch_yahoo_series should return a DataFrame with 'close' column and UTC DatetimeIndex."""
    dates = pd.date_range("2020-01-02", periods=5, freq="B", tz="America/New_York")
    mock_hist = pd.DataFrame(
        {
            "Open": [300.0, 301.0, 302.0, 303.0, 304.0],
            "High": [305.0, 306.0, 307.0, 308.0, 309.0],
            "Low": [295.0, 296.0, 297.0, 298.0, 299.0],
            "Close": [302.0, 303.0, 304.0, 305.0, 306.0],
            "Volume": [1000000, 1100000, 1200000, 1300000, 1400000],
        },
        index=dates,
    )

    with patch("yfinance.Ticker") as mock_ticker_cls:
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = mock_hist
        mock_ticker_cls.return_value = mock_ticker

        result = yahoo_fetcher.fetch_yahoo_series("AAPL", "2020-01-01", "2020-01-10")

    assert isinstance(result, pd.DataFrame)
    assert "close" in result.columns
    assert len(result) == 5
    assert result.index.tz is not None
    assert str(result.index.tz) == "UTC"
    assert result.index.name == "date"


def test_fetch_yahoo_invalid_ticker_raises():
    """An invalid ticker (empty DataFrame) should raise ValueError."""
    with patch("yfinance.Ticker") as mock_ticker_cls:
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = pd.DataFrame()
        mock_ticker_cls.return_value = mock_ticker

        with pytest.raises(ValueError, match="No data returned"):
            yahoo_fetcher.fetch_yahoo_series("INVALIDTICKER", "2020-01-01", "2020-12-31")
