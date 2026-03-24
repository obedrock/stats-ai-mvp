"""Tests for series_mapper.py — Claude tool-use for prompt → series ID mapping."""
from unittest.mock import MagicMock, patch

import pytest

from app.services import series_mapper


def _make_tool_use_response(sources: list[dict], date_range: dict | None = None) -> MagicMock:
    """Build a mock Anthropic response with a tool_use content block."""
    tool_use_block = MagicMock()
    tool_use_block.type = "tool_use"
    tool_use_block.input = {
        "sources": sources,
        "date_range": date_range or {"start": "2006-01-01", "end": "2026-01-01"},
    }

    response = MagicMock()
    response.content = [tool_use_block]
    return response


def test_map_prompt_detects_fred_source():
    """'GDP growth since 2000' should return a FRED source for GDPC1."""
    mock_sources = [
        {
            "source": "FRED",
            "series_id": "GDPC1",
            "display_name": "Real GDP",
            "rationale": "Real GDP measures economic growth.",
        }
    ]
    mock_response = _make_tool_use_response(mock_sources)

    with patch("app.services.series_mapper.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        result = series_mapper.map_prompt_to_sources("GDP growth since 2000")

    assert isinstance(result, dict)
    assert "sources" in result
    assert "date_range" in result
    assert len(result["sources"]) == 1
    assert result["sources"][0]["source"] == "FRED"
    assert result["sources"][0]["series_id"] == "GDPC1"


def test_map_prompt_detects_yahoo_source():
    """'AAPL price since 2020' should return a YAHOO source for AAPL."""
    mock_sources = [
        {
            "source": "YAHOO",
            "series_id": "AAPL",
            "display_name": "Apple Inc.",
            "rationale": "AAPL is the Yahoo Finance ticker for Apple.",
        }
    ]
    mock_response = _make_tool_use_response(mock_sources)

    with patch("app.services.series_mapper.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        result = series_mapper.map_prompt_to_sources("AAPL price since 2020")

    assert isinstance(result, dict)
    assert "sources" in result
    assert len(result["sources"]) == 1
    assert result["sources"][0]["source"] == "YAHOO"
    assert result["sources"][0]["series_id"] == "AAPL"


def test_map_prompt_multi_source():
    """'AAPL vs GDP since 2010' should return 2 sources (one FRED, one YAHOO)."""
    mock_sources = [
        {
            "source": "YAHOO",
            "series_id": "AAPL",
            "display_name": "Apple Inc.",
            "rationale": "AAPL is the Yahoo Finance ticker for Apple.",
        },
        {
            "source": "FRED",
            "series_id": "GDPC1",
            "display_name": "Real GDP",
            "rationale": "Real GDP measures economic growth.",
        },
    ]
    mock_response = _make_tool_use_response(mock_sources)

    with patch("app.services.series_mapper.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        result = series_mapper.map_prompt_to_sources("AAPL vs GDP since 2010")

    assert isinstance(result, dict)
    assert "sources" in result
    assert len(result["sources"]) == 2
    sources_set = {r["source"] for r in result["sources"]}
    assert "FRED" in sources_set
    assert "YAHOO" in sources_set
