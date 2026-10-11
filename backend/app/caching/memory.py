import asyncio
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any


@dataclass
class _Entry:
    value: Any
    expires_at: float


class InMemoryTTLCache:
    """Process-local cache with a TTL set per key (not per instance).

    Guards each key with its own lock in get_or_set so concurrent requests
    for the same missing key only trigger one upstream fetch (cache stampede
    protection), rather than one fetch per concurrent caller.
    """

    def __init__(self) -> None:
        self._store: dict[str, _Entry] = {}
        self._locks: dict[str, asyncio.Lock] = {}
        self._locks_guard = asyncio.Lock()

    async def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        if entry.expires_at < time.monotonic():
            del self._store[key]
            return None
        return entry.value

    async def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        self._store[key] = _Entry(
            value=value, expires_at=time.monotonic() + ttl_seconds
        )

    async def get_or_set(
        self,
        key: str,
        factory: Callable[[], Awaitable[Any]],
        ttl_seconds: int,
    ) -> Any:
        cached = await self.get(key)
        if cached is not None:
            return cached

        lock = await self._lock_for(key)
        async with lock:
            cached = await self.get(key)
            if cached is not None:
                return cached
            value = await factory()
            await self.set(key, value, ttl_seconds)
            return value

    async def _lock_for(self, key: str) -> asyncio.Lock:
        async with self._locks_guard:
            lock = self._locks.get(key)
            if lock is None:
                lock = asyncio.Lock()
                self._locks[key] = lock
            return lock
