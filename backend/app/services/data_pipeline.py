"""
Data cleaning and merging pipeline orchestrator.

Orchestrates: timezone normalization, missing value handling, unit normalization,
outlier detection, merging, and assumption tracking.

DATA-05: Missing value handling (forward-fill, interpolation, drop).
DATA-06: Timezone normalization to UTC.
DATA-07: Unit normalization (levels, percent change, log).
DATA-08: Outlier detection and flagging.
DATA-10: Smart assumptions engine (quick mode with documented defaults).
"""

import numpy as np
import pandas as pd


def clean_and_merge(
    dataframes: dict[str, pd.DataFrame],
    metadata: dict | None = None,
    mode: str = "quick",
) -> dict:
    """Clean, normalize, and merge a set of DataFrames.

    Applies transformations in order:
    1. Timezone normalization (all indexes -> UTC)
    2. Missing value handling (ffill <5%, interpolate 5-20%, drop >20%)
    3. Unit normalization (documents from metadata)
    4. Outlier detection (3-IQR, flag only — do not remove)
    5. Merge on date index (inner join)
    6. Build preview and column stats

    Args:
        dataframes: Mapping of series_id -> DataFrame with a DatetimeIndex.
        metadata: Optional metadata dict, e.g. {"GDPC1": {"unit": "billions"}}.
        mode: "quick" or "detailed". Quick mode applies smart defaults and
              documents them in assumptions.

    Returns:
        dict with keys:
          - merged_df: pd.DataFrame — cleaned and merged data
          - preview_rows: list[dict] — first 50 rows as records
          - column_stats: list[dict] — per-column stats (min, max, mean, missing_count)
          - assumptions: list[str] — descriptions of all transformations applied
          - total_rows: int — row count of merged result
          - outlier_flags: dict[str, int] — column name -> count of outliers detected
    """
    metadata = metadata or {}
    assumptions: list[str] = []
    cleaned: dict[str, pd.DataFrame] = {}

    # Step 1 — Timezone normalization (DATA-06)
    for series_id, df in dataframes.items():
        df = df.copy()
        if isinstance(df.index, pd.DatetimeIndex):
            if df.index.tz is None:
                df.index = df.index.tz_localize("UTC")
            elif str(df.index.tz) != "UTC":
                df.index = df.index.tz_convert("UTC")
        cleaned[series_id] = df

    assumptions.append("Normalized all date indexes to UTC")

    # Step 2 — Missing value handling (DATA-05)
    for series_id, df in cleaned.items():
        df = df.copy()
        for col in df.select_dtypes(include=[np.number]).columns:
            total = len(df)
            nan_count = int(df[col].isna().sum())
            if nan_count == 0:
                continue
            frac = nan_count / total if total > 0 else 0.0

            if frac < 0.05:
                df[col] = df[col].ffill()
                assumptions.append(
                    f"{series_id}: forward-filled {nan_count} missing value(s) in '{col}'"
                )
            elif frac <= 0.20:
                df[col] = df[col].interpolate(method="linear")
                assumptions.append(
                    f"{series_id}: interpolated {nan_count} missing value(s) in '{col}'"
                )
            else:
                before = len(df)
                df = df.dropna(subset=[col]).copy()
                after = len(df)
                assumptions.append(
                    f"{series_id}: dropped {before - after} row(s) with missing '{col}' (>{int(frac*100)}% missing)"
                )

        # Drop any remaining NaN rows after per-column strategy
        df = df.dropna().copy()
        cleaned[series_id] = df

    # Step 3 — Unit normalization (DATA-07)
    for series_id, df in cleaned.items():
        series_meta = metadata.get(series_id, {})
        unit = series_meta.get("unit")
        if unit == "billions":
            assumptions.append(f"{series_id} values in billions (no conversion needed)")
        elif unit in ("percentage", "percent"):
            assumptions.append(f"{series_id} expressed as percentage")
        elif unit == "index":
            assumptions.append(f"{series_id} is an index series (no unit conversion)")
        elif unit:
            assumptions.append(f"{series_id} unit: {unit}")

    # Step 4 — Outlier detection (DATA-08)
    outlier_flags: dict[str, int] = {}
    for series_id, df in cleaned.items():
        for col in df.select_dtypes(include=[np.number]).columns:
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1

            if iqr > 0:
                # Standard IQR method
                lower = q1 - 3 * iqr
                upper = q3 + 3 * iqr
                mask = (df[col] < lower) | (df[col] > upper)
            else:
                # IQR is 0 (all values identical or near-identical) — use Z-score fallback
                std = df[col].std()
                if std == 0:
                    continue
                z_scores = (df[col] - df[col].mean()).abs() / std
                mask = z_scores > 3

            count = int(mask.sum())
            if count > 0:
                outlier_flags[col] = outlier_flags.get(col, 0) + count
                assumptions.append(
                    f"{series_id}: {count} outlier value(s) detected in '{col}' (not removed)"
                )

    # Step 5 — Rename columns to series_id (all source DataFrames have a generic
    # "value" column; without renaming, pd.concat produces duplicate column names
    # and merged["value"] returns a DataFrame instead of a Series).
    for series_id, df in list(cleaned.items()):
        cleaned[series_id] = df.rename(columns={"value": series_id})

    if len(cleaned) == 1:
        merged = list(cleaned.values())[0].copy()
    else:
        merged = pd.concat(cleaned.values(), axis=1, join="inner").copy()

    assumptions.append(
        f"Merged {len(cleaned)} series on date index ({len(merged)} overlapping rows)"
    )

    # Step 6 — Build preview and column stats
    preview_rows = (
        merged.reset_index()
        .head(50)
        .to_dict(orient="records")
    )

    column_stats: list[dict] = []
    for col in merged.columns:
        if pd.api.types.is_numeric_dtype(merged[col]):
            column_stats.append({
                "name": col,
                "dtype": str(merged[col].dtype),
                "min": float(merged[col].min()),
                "max": float(merged[col].max()),
                "mean": float(merged[col].mean()),
                "missing_count": int(merged[col].isna().sum()),
            })
        else:
            column_stats.append({
                "name": col,
                "dtype": str(merged[col].dtype),
                "min": None,
                "max": None,
                "mean": None,
                "missing_count": int(merged[col].isna().sum()),
            })

    return {
        "merged_df": merged,
        "preview_rows": preview_rows,
        "column_stats": column_stats,
        "assumptions": assumptions,
        "total_rows": len(merged),
        "outlier_flags": outlier_flags,
    }
