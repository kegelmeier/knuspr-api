from __future__ import annotations

import time

from knuspr.rate_limiter import RateLimiter


class TestRateLimiter:
    def test_first_call_no_wait(self) -> None:
        limiter = RateLimiter(min_interval=0.1)
        start = time.monotonic()
        limiter.wait_sync()
        elapsed = time.monotonic() - start
        assert elapsed < 0.05  # first call should be near-instant

    def test_second_call_waits(self) -> None:
        limiter = RateLimiter(min_interval=0.1)
        limiter.wait_sync()
        start = time.monotonic()
        limiter.wait_sync()
        elapsed = time.monotonic() - start
        assert elapsed >= 0.08  # should wait ~100ms (with tolerance)

    def test_no_wait_after_enough_time(self) -> None:
        limiter = RateLimiter(min_interval=0.05)
        limiter.wait_sync()
        time.sleep(0.1)  # wait longer than interval
        start = time.monotonic()
        limiter.wait_sync()
        elapsed = time.monotonic() - start
        assert elapsed < 0.02  # should not wait

    def test_custom_interval(self) -> None:
        limiter = RateLimiter(min_interval=0.05)
        limiter.wait_sync()
        start = time.monotonic()
        limiter.wait_sync()
        elapsed = time.monotonic() - start
        assert elapsed >= 0.04
        assert elapsed < 0.1
