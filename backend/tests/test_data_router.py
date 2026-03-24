"""
Test stubs for data router API endpoints (DATA-02, DATA-09, DATA-11, DATA-16).

DATA-02: Parse user prompt and return detected data sources + series IDs.
DATA-09: Detect frequency conflicts and return resolution options via API.
DATA-11: User source override endpoint (change FRED to Yahoo or vice versa).
DATA-16: Data preview endpoint — return cleaned/merged dataset before analysis.
Implementation target: Plan 08 (data router integration).
"""

import pytest


def test_parse_prompt_endpoint():
    """POST /data/parse-prompt should return detected sources and series for a valid prompt."""
    pytest.skip("Wave 0 stub -- implementation in Plan 08")


def test_override_source():
    """POST /data/override-source should substitute the specified source for a series."""
    pytest.skip("Wave 0 stub -- implementation in Plan 08")


def test_frequency_conflict_returned():
    """When merging daily and quarterly series, GET /data/fetch should return frequency_conflict."""
    pytest.skip("Wave 0 stub -- implementation in Plan 08")


def test_assumptions_detailed_gate():
    """Detailed mode should return assumption list before executing rather than running immediately."""
    pytest.skip("Wave 0 stub -- implementation in Plan 08")


def test_preview_response():
    """GET /data/preview should return the merged and cleaned dataset as paginated JSON."""
    pytest.skip("Wave 0 stub -- implementation in Plan 08")
