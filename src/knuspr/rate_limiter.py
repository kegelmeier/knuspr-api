import asyncio
import time


class RateLimiter:
    def __init__(self, min_interval: float = 0.1):
        self._min_interval = min_interval
        self._last_request: float = 0.0

    def wait_sync(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_request
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_request = time.monotonic()

    async def wait_async(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_request
        if elapsed < self._min_interval:
            await asyncio.sleep(self._min_interval - elapsed)
        self._last_request = time.monotonic()
