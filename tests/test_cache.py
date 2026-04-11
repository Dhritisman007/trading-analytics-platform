# tests/test_cache.py

import time

import pytest
from fastapi.testclient import TestClient

from core.cache import TTLCache
from main import app

client = TestClient(app)


class TestTTLCache:

    def setup_method(self):
        """Fresh cache for every test."""
        self.cache = TTLCache()

    def test_set_and_get_returns_value(self):
        self.cache.set("key1", {"data": 42}, ttl_seconds=60)
        result = self.cache.get("key1")
        assert result == {"data": 42}

    def test_get_missing_key_returns_none(self):
        result = self.cache.get("nonexistent")
        assert result is None

    def test_expired_entry_returns_none(self):
        self.cache.set("short", "value", ttl_seconds=1)
        time.sleep(1.1)
        result = self.cache.get("short")
        assert result is None

    def test_live_entry_not_expired(self):
        self.cache.set("live", "value", ttl_seconds=60)
        result = self.cache.get("live")
        assert result == "value"

    def test_delete_removes_entry(self):
        self.cache.set("to_delete", "value", ttl_seconds=60)
        self.cache.delete("to_delete")
        assert self.cache.get("to_delete") is None

    def test_clear_wipes_all_entries(self):
        self.cache.set("a", 1, ttl_seconds=60)
        self.cache.set("b", 2, ttl_seconds=60)
        self.cache.clear()
        assert self.cache.get("a") is None
        assert self.cache.get("b") is None

    def test_overwrite_updates_value(self):
        self.cache.set("key", "old", ttl_seconds=60)
        self.cache.set("key", "new", ttl_seconds=60)
        assert self.cache.get("key") == "new"

    def test_stats_returns_correct_live_count(self):
        self.cache.set("x", 1, ttl_seconds=60)
        self.cache.set("y", 2, ttl_seconds=60)
        stats = self.cache.stats()
        assert stats["live"] == 2
        assert stats["total_entries"] == 2

    def test_stats_counts_expired_correctly(self):
        self.cache.set("fast", "gone", ttl_seconds=1)
        time.sleep(1.1)
        # Force a get to trigger cleanup
        self.cache.get("fast")
        stats = self.cache.stats()
        assert stats["live"] == 0


class TestCacheEndpoints:

    def test_cache_stats_returns_200(self):
        r = client.get("/cache/stats")
        assert r.status_code == 200

    def test_cache_stats_has_required_keys(self):
        r = client.get("/cache/stats")
        data = r.json()
        assert "total_entries" in data
        assert "live" in data
        assert "keys" in data

    def test_cache_clear_returns_200(self):
        r = client.delete("/cache/clear")
        assert r.status_code == 200

    def test_market_endpoint_uses_cache_on_second_call(self):
        # First call populates cache
        r1 = client.get("/market/?period=1mo")
        assert r1.status_code == 200
        # Second call should be served from cache — still 200
        r2 = client.get("/market/?period=1mo")
        assert r2.status_code == 200
        # Both responses should be identical
        assert r1.json()["count"] == r2.json()["count"]
