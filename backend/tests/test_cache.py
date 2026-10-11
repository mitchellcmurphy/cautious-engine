import asyncio

import pytest

from app.caching.memory import InMemoryTTLCache


async def test_set_then_get_returns_value():
    cache = InMemoryTTLCache()
    await cache.set("k", "v", ttl_seconds=60)
    assert await cache.get("k") == "v"


async def test_get_missing_key_returns_none():
    cache = InMemoryTTLCache()
    assert await cache.get("missing") is None


async def test_expired_entry_returns_none():
    cache = InMemoryTTLCache()
    await cache.set("k", "v", ttl_seconds=0)
    await asyncio.sleep(0.01)
    assert await cache.get("k") is None


async def test_get_or_set_calls_factory_once_on_miss():
    cache = InMemoryTTLCache()
    calls = 0

    async def factory():
        nonlocal calls
        calls += 1
        return "computed"

    result = await cache.get_or_set("k", factory, ttl_seconds=60)
    assert result == "computed"
    assert calls == 1

    # second call should hit cache, not factory
    result2 = await cache.get_or_set("k", factory, ttl_seconds=60)
    assert result2 == "computed"
    assert calls == 1


async def test_get_or_set_stampede_protection():
    cache = InMemoryTTLCache()
    calls = 0

    async def factory():
        nonlocal calls
        calls += 1
        await asyncio.sleep(0.05)
        return "computed"

    results = await asyncio.gather(
        *(cache.get_or_set("k", factory, ttl_seconds=60) for _ in range(10))
    )

    assert all(r == "computed" for r in results)
    assert calls == 1


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main([__file__, "-v"]))
