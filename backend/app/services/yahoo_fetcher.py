"""Yahoo Finance data fetching.

Wraps the yfinance 1.x API to fetch daily OHLCV data and returns a clean
DataFrame with UTC-converted DatetimeIndex and a "close" column.
"""
import pandas as pd
import yfinance as yf


def fetch_yahoo_series(symbol: str, start: str, end: str) -> pd.DataFrame:
    """Fetch daily closing prices for a Yahoo Finance symbol.

    Args:
        symbol: Yahoo Finance ticker symbol (e.g., "AAPL", "SPY").
        start: Start date string in YYYY-MM-DD format.
        end: End date string in YYYY-MM-DD format.

    Returns:
        DataFrame with a UTC DatetimeIndex named "date" and a "close" column.
        Uses .copy() explicitly per pandas 3.0 Copy-on-Write semantics.

    Raises:
        ValueError: If no data is returned for the given symbol/date range.
    """
    ticker = yf.Ticker(symbol)
    hist = ticker.history(start=start, end=end, interval="1d")

    if hist.empty:
        raise ValueError(
            f"No data returned for ticker '{symbol}'. "
            "Verify the symbol is valid and the date range contains trading days."
        )

    # Select close column and rename — .copy() per pandas 3.0 CoW
    df = hist[["Close"]].rename(columns={"Close": "close"}).copy()

    # Yahoo returns tz-aware index; convert to UTC per Pitfall 4
    df.index = df.index.tz_convert("UTC")
    df.index.name = "date"

    return df
