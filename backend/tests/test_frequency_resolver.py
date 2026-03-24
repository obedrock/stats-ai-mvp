"""
Tests for frequency mismatch detection and resolution (DATA-09).

DATA-09: Detect frequency conflicts between merged datasets and surface
resolution options (aggregate, interpolate, or abort) to the user.
"""

import pandas as pd
import pytest


def _make_daily_df(n: int = 252) -> pd.DataFrame:
    """Create a daily-frequency DataFrame with a DatetimeIndex."""
    idx = pd.date_range("2020-01-01", periods=n, freq="B")
    return pd.DataFrame({"price": range(n)}, index=idx)


def _make_quarterly_df(n: int = 8) -> pd.DataFrame:
    """Create a quarterly-frequency DataFrame with a DatetimeIndex."""
    idx = pd.date_range("2020-01-01", periods=n, freq="QS")
    return pd.DataFrame({"gdp": [20000 + i * 100 for i in range(n)]}, index=idx)


def test_detect_frequencies_daily_vs_quarterly():
    """Merging a daily series and a quarterly series should detect different frequencies."""
    from app.services.frequency_resolver import detect_frequencies

    dataframes = {
        "AAPL": _make_daily_df(),
        "GDP": _make_quarterly_df(),
    }
    freqs = detect_frequencies(dataframes)

    assert "AAPL" in freqs
    assert "GDP" in freqs

    # Daily freq should be "B" (business days) or "D"
    assert freqs["AAPL"] in ("B", "D", "C")
    # Quarterly freq should be "QS" or "QS-OCT" or similar
    assert freqs["GDP"].startswith("QS") or freqs["GDP"].startswith("Q")


def test_check_frequency_conflict_detects_mismatch():
    """check_frequency_conflict should return has_conflict=True for daily vs quarterly."""
    from app.services.frequency_resolver import check_frequency_conflict

    dataframes = {
        "AAPL": _make_daily_df(),
        "GDP": _make_quarterly_df(),
    }
    result = check_frequency_conflict(dataframes)

    assert result["has_conflict"] is True
    assert len(result["series_frequencies"]) == 2
    assert result["target_frequency"] != ""
    assert result["recommended_method"] in ("mean", "last", "sum", "ffill")
    assert len(result["recommendation"]) > 0


def test_check_frequency_no_conflict_same_freq():
    """check_frequency_conflict should return has_conflict=False for same-frequency series."""
    from app.services.frequency_resolver import check_frequency_conflict

    dataframes = {
        "GDP1": _make_quarterly_df(8),
        "GDP2": _make_quarterly_df(8),
    }
    result = check_frequency_conflict(dataframes)

    assert result["has_conflict"] is False


def test_apply_resolution_mean():
    """Aggregating a daily series to quarterly using mean should reduce row count."""
    from app.services.frequency_resolver import apply_resolution

    daily_df = _make_daily_df(252)
    result = apply_resolution(daily_df, "QS", "mean")

    # Daily 252 rows -> quarterly ~4-5 rows
    assert len(result) < len(daily_df)
    assert len(result) >= 4


def test_apply_resolution_ffill():
    """Forward-filling a quarterly series to daily should increase row count."""
    from app.services.frequency_resolver import apply_resolution

    quarterly_df = _make_quarterly_df(8)
    result = apply_resolution(quarterly_df, "D", "ffill")

    # Quarterly 8 rows -> daily many more rows
    assert len(result) > len(quarterly_df)


def test_apply_resolution_unknown_raises():
    """Unknown resolution method should raise ValueError."""
    from app.services.frequency_resolver import apply_resolution

    with pytest.raises(ValueError, match="Unknown resolution method"):
        apply_resolution(_make_daily_df(), "QS", "unknown_method")
