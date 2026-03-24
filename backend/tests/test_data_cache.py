"""Tests for data_cache.py — Redis get/set with TTL helpers."""
import time
from unittest.mock import patch

import fakeredis
import pytest

from app.services import data_cache


@pytest.fixture(autouse=True)
def fake_redis_client():
    """Inject a fakeredis client for all tests in this module."""
    client = fakeredis.FakeRedis()
    data_cache.init_redis(client)
    yield client
    # Reset module-level state after each test
    data_cache.init_redis(None)


def test_set_and_get_cached(fake_redis_client):
    """set_cached then get_cached should return the same JSON string."""
    key = "fred:GDPC1:2000:2023"
    value = '{"data": [1, 2, 3]}'
    data_cache.set_cached(key, value, 86400)

    result = data_cache.get_cached(key)
    assert result == value


def test_cache_miss_returns_none():
    """get_cached on a key that doesn't exist should return None."""
    result = data_cache.get_cached("nonexistent:key:12345")
    assert result is None


def test_cache_ttl_expiry():
    """After TTL expires, get_cached should return None.

    Patches time.time to advance the clock without sleeping.
    """
    server = fakeredis.FakeServer()
    client = fakeredis.FakeRedis(server=server)
    data_cache.init_redis(client)

    key = "yahoo:AAPL:2020:2023"
    value = '{"close": [150.0]}'

    start = time.time()
    data_cache.set_cached(key, value, ttl=1)

    # Advance the clock by 2 seconds so the 1s TTL has expired
    with patch("time.time", return_value=start + 2):
        result = data_cache.get_cached(key)

    assert result is None
