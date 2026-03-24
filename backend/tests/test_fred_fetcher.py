"""Tests for fred_fetcher.py — FRED series validation and data fetching."""
from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import pytest

from app.services import fred_fetcher


@pytest.mark.asyncio
async def test_validate_series_valid_id():
    """A valid FRED series ID should return (True, [])."""
    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        with patch.dict("os.environ", {"FRED_API_KEY": "test_key"}):
            result = await fred_fetcher.validate_series("GDPC1")

    assert result == (True, [])


@pytest.mark.asyncio
async def test_validate_series_invalid_returns_suggestions():
    """An invalid FRED series ID should return (False, list_of_suggestions)."""
    mock_response = MagicMock()
    mock_response.status_code = 400

    # Build a mock search result DataFrame with 3 rows
    search_df = pd.DataFrame(
        {
            "title": ["Real GDP", "Nominal GDP", "GDP Deflator"],
        },
        index=["GDPC1", "GDP", "GDPDEF"],
    )

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        with patch("fredapi.Fred") as mock_fred_cls:
            mock_fred = MagicMock()
            mock_fred.search.return_value = search_df
            mock_fred_cls.return_value = mock_fred

            with patch.dict("os.environ", {"FRED_API_KEY": "test_key"}):
                is_valid, suggestions = await fred_fetcher.validate_series("BADID")

    assert is_valid is False
    assert len(suggestions) == 3
    assert suggestions[0]["id"] == "GDPC1"
    assert suggestions[0]["name"] == "Real GDP"


def test_fetch_fred_series_returns_dataframe():
    """fetch_fred_series should return a DataFrame with 'value' column and UTC DatetimeIndex."""
    dates = pd.date_range("2000-01-01", periods=5, freq="QS")
    mock_series = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0], index=dates)

    with patch("fredapi.Fred") as mock_fred_cls:
        mock_fred = MagicMock()
        mock_fred.get_series.return_value = mock_series
        mock_fred_cls.return_value = mock_fred

        with patch.dict("os.environ", {"FRED_API_KEY": "test_key"}):
            result = fred_fetcher.fetch_fred_series("GDPC1", "2000-01-01", "2001-01-01")

    assert isinstance(result, pd.DataFrame)
    assert "value" in result.columns
    assert len(result) == 5
    assert result.index.tz is not None
    assert str(result.index.tz) == "UTC"
    assert result.index.name == "date"
