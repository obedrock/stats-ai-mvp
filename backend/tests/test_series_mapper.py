"""
Test stubs for series mapper (DATA-01).

DATA-01: Auto-detect data source from natural language prompt.
Implementation target: Plan 03 (series mapper + FRED fetcher).
"""

import pytest


def test_map_prompt_detects_fred_source():
    """Prompt mentioning GDP should map to FRED source."""
    pytest.skip("Wave 0 stub -- implementation in Plan 03")


def test_map_prompt_detects_yahoo_source():
    """Prompt mentioning AAPL stock price should map to Yahoo Finance."""
    pytest.skip("Wave 0 stub -- implementation in Plan 03")


def test_map_prompt_multi_source():
    """Prompt with both macro data and stock price should detect both sources."""
    pytest.skip("Wave 0 stub -- implementation in Plan 03")
