"""
Tests for data pipeline cleaning and transformation (DATA-05, 06, 07, 08, 10).

DATA-05: Missing value handling (forward-fill, interpolation, drop).
DATA-06: Timezone normalization to UTC.
DATA-07: Unit normalization (levels, percent change, log).
DATA-08: Outlier detection and flagging.
DATA-10: Smart assumptions engine (quick mode with documented defaults).
"""

import numpy as np
import pandas as pd
import pytest


def _make_df_with_missing(missing_frac: float = 0.03) -> pd.DataFrame:
    """Create a DataFrame with a known fraction of NaN values."""
    idx = pd.date_range("2020-01-01", periods=100, freq="D", tz="UTC")
    values = list(range(100))
    n_missing = int(100 * missing_frac)
    for i in range(n_missing):
        values[i * (100 // (n_missing + 1))] = None
    return pd.DataFrame({"gdp": values}, index=idx)


def test_missing_value_handling():
    """Pipeline should forward-fill or interpolate missing values per strategy."""
    from app.services.data_pipeline import clean_and_merge

    df = _make_df_with_missing(missing_frac=0.03)
    result = clean_and_merge({"GDPC1": df})

    # After cleaning, NaN count should be 0 (or at least reduced)
    merged = result["merged_df"]
    assert merged["gdp"].isna().sum() == 0

    # Assumptions should mention what strategy was used
    assumptions_text = " ".join(result["assumptions"]).lower()
    assert any(kw in assumptions_text for kw in ["forward-fill", "ffill", "interpolat", "drop"])


def test_timezone_alignment():
    """All timestamps should be normalized to UTC regardless of source timezone."""
    from app.services.data_pipeline import clean_and_merge

    idx_naive = pd.date_range("2020-01-01", periods=50, freq="D")
    idx_eastern = pd.date_range("2020-01-01", periods=50, freq="D", tz="US/Eastern")

    df_naive = pd.DataFrame({"gdp": range(50)}, index=idx_naive)
    df_eastern = pd.DataFrame({"cpi": range(50)}, index=idx_eastern)

    result = clean_and_merge({"GDP": df_naive, "CPI": df_eastern})

    merged = result["merged_df"]
    # Index must be timezone-aware UTC
    assert merged.index.tz is not None
    assert str(merged.index.tz) == "UTC"

    assumptions_text = " ".join(result["assumptions"]).lower()
    assert "utc" in assumptions_text


def test_unit_normalization():
    """Metadata unit hints should be logged in assumptions."""
    from app.services.data_pipeline import clean_and_merge

    idx = pd.date_range("2020-01-01", periods=10, freq="MS", tz="UTC")
    df = pd.DataFrame({"gdp": [20000 + i * 100 for i in range(10)]}, index=idx)

    metadata = {"GDPC1": {"unit": "billions"}, "DFF": {"unit": "percentage"}}
    result = clean_and_merge({"GDPC1": df}, metadata=metadata)

    assumptions_text = " ".join(result["assumptions"]).lower()
    assert "billion" in assumptions_text or "gdpc1" in assumptions_text


def test_outlier_detection():
    """Outliers beyond 3 IQR should be flagged but NOT removed."""
    from app.services.data_pipeline import clean_and_merge

    idx = pd.date_range("2020-01-01", periods=50, freq="D", tz="UTC")
    values = [100.0] * 50
    values[25] = 10000.0  # Extreme outlier

    df = pd.DataFrame({"price": values}, index=idx)
    result = clean_and_merge({"AAPL": df})

    merged = result["merged_df"]
    # Outlier must NOT be removed
    assert 10000.0 in merged["price"].values

    # outlier_flags should record count
    assert result["outlier_flags"].get("price", 0) >= 1

    # Assumptions should mention outlier
    assumptions_text = " ".join(result["assumptions"]).lower()
    assert "outlier" in assumptions_text


def test_assumptions_quick_mode():
    """Quick mode should produce a non-empty assumptions list describing transformations."""
    from app.services.data_pipeline import clean_and_merge

    idx = pd.date_range("2020-01-01", periods=20, freq="D", tz="UTC")
    df = pd.DataFrame({"gdp": range(20)}, index=idx)

    result = clean_and_merge({"GDP": df}, mode="quick")

    assert isinstance(result["assumptions"], list)
    assert len(result["assumptions"]) > 0

    # Verify all required output keys are present
    assert "merged_df" in result
    assert "preview_rows" in result
    assert "column_stats" in result
    assert "total_rows" in result
    assert "outlier_flags" in result
