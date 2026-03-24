"""FRED series validation and data fetching.

Validates series IDs against the FRED REST API before use (per D-02).
Falls back to Fred.search() for suggestions on invalid IDs.
Fetches data via fredapi and normalizes DatetimeIndex to UTC.
"""
import httpx
import pandas as pd

FRED_BASE = "https://api.stlouisfed.org/fred"


async def validate_series(series_id: str) -> tuple[bool, list[dict]]:
    """Validate a FRED series ID against the FRED REST API.

    Args:
        series_id: FRED series identifier (e.g., "GDPC1", "CPIAUCSL").

    Returns:
        (True, []) if the series exists.
        (False, suggestions) if the series is invalid, where suggestions
        is a list of dicts with keys "id" and "name".
    """
    from app.config import settings
    api_key = settings.fred_api_key
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{FRED_BASE}/series",
            params={"series_id": series_id, "api_key": api_key, "file_type": "json"},
            timeout=10.0,
        )
    if r.status_code == 200:
        return True, []

    # Search for alternatives
    import fredapi

    fred = fredapi.Fred(api_key=api_key)
    results = fred.search(series_id, limit=5)
    suggestions = [{"id": str(idx), "name": row["title"]} for idx, row in results.iterrows()]
    return False, suggestions


def fetch_fred_series(series_id: str, start: str, end: str) -> pd.DataFrame:
    """Fetch a FRED data series as a DataFrame with UTC-localized DatetimeIndex.

    Args:
        series_id: FRED series identifier (e.g., "GDPC1").
        start: Start date string in YYYY-MM-DD format.
        end: End date string in YYYY-MM-DD format.

    Returns:
        DataFrame with a UTC DatetimeIndex named "date" and a "value" column.
        Uses .copy() explicitly per pandas 3.0 Copy-on-Write semantics.
    """
    import fredapi

    from app.config import settings
    api_key = settings.fred_api_key
    fred = fredapi.Fred(api_key=api_key)
    series = fred.get_series(series_id, observation_start=start, observation_end=end)

    # Convert to DataFrame — .copy() required for pandas 3.0 CoW
    df = series.to_frame(name="value").copy()

    # FRED returns tz-naive DatetimeIndex; localize to UTC per Pitfall 4
    df.index = pd.DatetimeIndex(df.index).tz_localize("UTC")
    df.index.name = "date"

    return df
