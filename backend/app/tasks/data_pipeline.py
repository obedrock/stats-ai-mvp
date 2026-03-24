"""Celery task for data fetching pipeline.

Orchestrates: fetch from FRED/Yahoo, cache, frequency conflict detection,
resolution application, cleaning, and merging.

DATA-15: Cache fetched data in Redis with source-appropriate TTL.
DATA-09: Detect and return frequency conflicts to the frontend.
"""
import json

import pandas as pd

from .celery_app import celery_app
from app.services.data_cache import get_cached, set_cached
from app.services.data_pipeline import clean_and_merge
from app.services.fred_fetcher import fetch_fred_series
from app.services.frequency_resolver import apply_resolution, check_frequency_conflict
from app.services.yahoo_fetcher import fetch_yahoo_series


@celery_app.task(bind=True, name="fetch_data")
def fetch_data(
    self,
    job_id: str,
    sources: list,
    date_range: dict,
    mode: str = "quick",
    resolution: dict | None = None,
):
    """Fetch data from all sources, cache, clean, merge, and return preview.

    Args:
        job_id: The job UUID string for progress tracking.
        sources: List of source dicts with keys: source, series_id, display_name, rationale.
        date_range: Dict with "start" and "end" date strings (YYYY-MM-DD).
        mode: "quick" or "detailed" — controls assumption documentation verbosity.
        resolution: Optional dict with "method" and "target_frequency" for resolving
                    a previously detected frequency conflict.

    Returns:
        Dict with status "data_ready" and preview data, or status "frequency_conflict"
        when a mismatch is detected and no resolution was provided.
    """
    dataframes: dict[str, pd.DataFrame] = {}
    cache_keys: list[str] = []

    for source_info in sources:
        source = source_info["source"]
        series_id = source_info["series_id"]
        start = date_range["start"]
        end = date_range["end"]
        cache_key = f"{source.lower()}:{series_id}:{start}:{end}"
        cache_keys.append(cache_key)

        # Check cache first (DATA-15)
        cached = get_cached(cache_key)
        if cached:
            self.update_state(
                state="PROGRESS",
                meta={
                    "stage": "fetching_data",
                    "job_id": job_id,
                    "sub_status": f"Cache hit: {source}: {series_id}",
                },
            )
            df = pd.read_json(cached)
            # IMPORTANT: Restore UTC timezone on cached DataFrames before
            # frequency conflict check. pd.read_json loses timezone info,
            # and check_frequency_conflict requires consistent UTC indexes
            # (clean_and_merge's timezone normalization happens later).
            if df.index.tz is None:
                df.index = df.index.tz_localize("UTC")
            dataframes[series_id] = df
            continue

        self.update_state(
            state="PROGRESS",
            meta={
                "stage": "fetching_data",
                "job_id": job_id,
                "sub_status": f"Fetching {source}: {series_id}...",
            },
        )

        if source == "FRED":
            df = fetch_fred_series(series_id, start, end)
        elif source == "YAHOO":
            df = fetch_yahoo_series(series_id, start, end)
        else:
            raise ValueError(f"Unknown source: {source}")

        # Cache with appropriate TTL (FRED=24h, Yahoo=1h per CLAUDE.md)
        ttl = 86400 if source == "FRED" else 3600
        set_cached(cache_key, df.to_json(), ttl)
        dataframes[series_id] = df

    # Check frequency conflict (DATA-09)
    if len(dataframes) > 1:
        conflict = check_frequency_conflict(dataframes)
        if conflict["has_conflict"] and resolution:
            # Apply user-confirmed resolution
            for series_id, df in list(dataframes.items()):
                dataframes[series_id] = apply_resolution(
                    df, resolution["target_frequency"], resolution["method"]
                )
        elif conflict["has_conflict"] and not resolution:
            # Return conflict to frontend -- task pauses here
            return {
                "status": "frequency_conflict",
                "job_id": job_id,
                "conflict": conflict,
                "cache_keys": cache_keys,
            }

    # Clean and merge (DATA-05, 06, 07, 08, 10)
    self.update_state(
        state="PROGRESS",
        meta={
            "stage": "fetching_data",
            "job_id": job_id,
            "sub_status": "Cleaning and merging data...",
        },
    )
    result = clean_and_merge(dataframes, mode=mode)

    return {
        "status": "data_ready",
        "job_id": job_id,
        "preview_rows": result["preview_rows"],
        "column_stats": result["column_stats"],
        "assumptions": result["assumptions"],
        "total_rows": result["total_rows"],
        "cache_keys": cache_keys,
    }
