"""
Frequency detection and resolution service.

Detects frequency mismatches between fetched series and provides resampling
functions to resolve them per user choice.

DATA-09: Detect frequency conflicts between merged datasets and surface
resolution options to the user.
"""

import pandas as pd


# Frequency ordering: lower index = higher frequency
# Used to determine the lowest frequency (target) when there's a mismatch
_FREQ_ORDER = ["T", "H", "D", "B", "C", "W", "SMS", "MS", "ME", "QS", "QE", "YS", "YE", "A"]


def _freq_rank(freq_str: str) -> int:
    """Return the rank of a frequency string (higher = lower frequency)."""
    if freq_str is None or freq_str == "irregular":
        return -1
    # Normalize — strip trailing numbers/letters after the base alias
    base = freq_str.split("-")[0]  # e.g. "QS-OCT" -> "QS"
    try:
        return _FREQ_ORDER.index(base)
    except ValueError:
        return -1


def detect_frequencies(dataframes: dict[str, pd.DataFrame]) -> dict[str, str]:
    """Infer the time frequency of each DataFrame's index.

    Args:
        dataframes: Mapping of series_id -> DataFrame with a DatetimeIndex.

    Returns:
        Mapping of series_id -> frequency string (e.g., "B", "D", "QS", "irregular").
    """
    result: dict[str, str] = {}
    for series_id, df in dataframes.items():
        if not isinstance(df.index, pd.DatetimeIndex) or len(df) < 2:
            result[series_id] = "irregular"
            continue
        freq = pd.infer_freq(df.index)
        result[series_id] = freq if freq is not None else "irregular"
    return result


def check_frequency_conflict(dataframes: dict[str, pd.DataFrame]) -> dict:
    """Check whether the provided DataFrames have conflicting time frequencies.

    Args:
        dataframes: Mapping of series_id -> DataFrame with a DatetimeIndex.

    Returns:
        A dict shaped like FrequencyConflict schema:
          - has_conflict: bool
          - series_frequencies: list[{series_id, frequency, row_count}]
          - recommendation: str
          - recommended_method: str
          - target_frequency: str
    """
    freqs = detect_frequencies(dataframes)

    series_frequencies = [
        {"series_id": sid, "frequency": freq, "row_count": len(dataframes[sid])}
        for sid, freq in freqs.items()
    ]

    # Consider only non-irregular frequencies for conflict detection
    valid_freqs = {sid: f for sid, f in freqs.items() if f != "irregular"}
    unique_freqs = set(valid_freqs.values())

    if len(unique_freqs) <= 1:
        return {
            "has_conflict": False,
            "series_frequencies": series_frequencies,
            "recommendation": "",
            "recommended_method": "",
            "target_frequency": list(unique_freqs)[0] if unique_freqs else "",
        }

    # Multiple distinct frequencies — find the lowest frequency (least granular) as target
    ranked = sorted(valid_freqs.items(), key=lambda item: _freq_rank(item[1]), reverse=True)
    target_sid, target_freq = ranked[0]

    # Identify which series need to be aggregated vs upsampled
    high_freq_series = [sid for sid, f in valid_freqs.items() if f != target_freq]
    recommendation = (
        f"Aggregate {', '.join(high_freq_series)} to {target_freq} via mean"
    )

    return {
        "has_conflict": True,
        "series_frequencies": series_frequencies,
        "recommendation": recommendation,
        "recommended_method": "mean",
        "target_frequency": target_freq,
    }


def apply_resolution(df: pd.DataFrame, target_freq: str, method: str) -> pd.DataFrame:
    """Resample or align a DataFrame to the target frequency using the chosen method.

    Args:
        df: DataFrame with a DatetimeIndex.
        target_freq: Target pandas frequency string (e.g., "QS", "D", "MS").
        method: Resampling method: "mean", "last", "sum" for downsampling;
                "ffill" for upsampling via forward-fill.

    Returns:
        Resampled DataFrame (copy, per pandas 3.0 CoW semantics).

    Raises:
        ValueError: If method is not one of the supported options.
    """
    if method in ("mean", "last", "sum"):
        return df.resample(target_freq).agg(method).copy()
    elif method == "ffill":
        return df.asfreq(target_freq, method="ffill").copy()
    else:
        raise ValueError(
            f"Unknown resolution method: {method!r}. "
            f"Supported methods: 'mean', 'last', 'sum', 'ffill'"
        )
