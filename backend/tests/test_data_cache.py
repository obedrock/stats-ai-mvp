"""
Test stubs for Redis dataset caching (DATA-15).

DATA-15: Cache fetched datasets in Redis to reduce redundant API calls.
Key format: {source}:{series_id}:{start}:{end}
TTL: FRED = 24h, Yahoo Finance = 1h.
Implementation target: Plan 06 (data cache layer).
"""

import pytest


def test_set_and_get_cached():
    """Setting a dataset in cache and retrieving it should return identical data."""
    pytest.skip("Wave 0 stub -- implementation in Plan 06")


def test_cache_miss_returns_none():
    """Cache miss for an unknown key should return None without error."""
    pytest.skip("Wave 0 stub -- implementation in Plan 06")


def test_cache_ttl_expiry():
    """Cached entry should be absent after TTL expiry."""
    pytest.skip("Wave 0 stub -- implementation in Plan 06")
