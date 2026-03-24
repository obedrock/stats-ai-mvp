"""
Test stubs for frequency mismatch detection and resolution (DATA-09).

DATA-09: Detect frequency conflicts between merged datasets and surface
resolution options (aggregate, interpolate, or abort) to the user.
Implementation target: Plan 05 (data cleaning pipeline).
"""

import pytest


def test_detect_frequencies_daily_vs_quarterly():
    """Merging a daily series and a quarterly series should detect a frequency conflict."""
    pytest.skip("Wave 0 stub -- implementation in Plan 05")


def test_apply_resolution_mean():
    """Aggregating a daily series to quarterly using mean should produce correct output."""
    pytest.skip("Wave 0 stub -- implementation in Plan 05")


def test_apply_resolution_ffill():
    """Interpolating a quarterly series to daily using forward-fill should produce correct output."""
    pytest.skip("Wave 0 stub -- implementation in Plan 05")
