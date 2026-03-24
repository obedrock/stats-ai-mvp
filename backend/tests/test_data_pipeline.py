"""
Test stubs for data pipeline cleaning and transformation (DATA-05, 06, 07, 08, 10).

DATA-05: Missing value handling (forward-fill, interpolation, drop).
DATA-06: Timezone normalization to UTC.
DATA-07: Unit normalization (levels, percent change, log).
DATA-08: Outlier detection and flagging.
DATA-10: Smart assumptions engine (quick mode with documented defaults).
Implementation target: Plan 05 (data cleaning pipeline).
"""

import pytest


def test_missing_value_handling():
    """Pipeline should forward-fill or interpolate missing values per strategy."""
    pytest.skip("Wave 0 stub -- implementation in Plan 05")


def test_timezone_alignment():
    """All timestamps should be normalized to UTC regardless of source timezone."""
    pytest.skip("Wave 0 stub -- implementation in Plan 05")


def test_unit_normalization():
    """Levels, percent-change, and log transforms should produce correct output."""
    pytest.skip("Wave 0 stub -- implementation in Plan 05")


def test_outlier_detection():
    """Outliers beyond 3 IQR should be flagged with row index and value."""
    pytest.skip("Wave 0 stub -- implementation in Plan 05")


def test_assumptions_quick_mode():
    """Quick mode should apply smart defaults and include assumption summary in result."""
    pytest.skip("Wave 0 stub -- implementation in Plan 05")
