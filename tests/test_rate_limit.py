"""Tests for the in-process sliding-window rate limiter."""

from collections.abc import Generator
from typing import Any

import pytest

from hector.services.rate_limit import SlidingWindowLimiter, get_login_limiter


class FakeClock:
    """Deterministic monotonic clock for limiter tests."""

    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def clock() -> FakeClock:
    """Fresh deterministic clock per test."""
    return FakeClock()


@pytest.fixture(autouse=True)
def reset_login_limiter() -> Generator[None, Any, None]:
    """Keep endpoint-level limiter state isolated between tests."""
    get_login_limiter().reset_all()
    yield
    get_login_limiter().reset_all()


def test_blocks_after_threshold(clock: FakeClock) -> None:
    """Blocking kicks in exactly at max_failures."""
    limiter = SlidingWindowLimiter(max_failures=5, window_seconds=900, clock=clock)

    for _ in range(5):
        blocked, _retry = limiter.check("ip1")
        assert blocked is False
        limiter.record_failure("ip1")

    blocked, retry = limiter.check("ip1")
    assert blocked is True
    assert retry == 900


def test_window_expiry_unblocks(clock: FakeClock) -> None:
    """Failures older than the window no longer block."""
    limiter = SlidingWindowLimiter(max_failures=2, window_seconds=900, clock=clock)

    limiter.record_failure("ip1")
    clock.now += 400
    limiter.record_failure("ip1")
    blocked, _ = limiter.check("ip1")
    assert blocked is True

    clock.now += 501  # first failure now outside the window
    blocked, retry = limiter.check("ip1")
    assert blocked is False
    assert retry == 0


def test_reset_clears_failures(clock: FakeClock) -> None:
    """A single key can be cleared."""
    limiter = SlidingWindowLimiter(max_failures=2, window_seconds=900, clock=clock)

    limiter.record_failure("ip1")
    limiter.reset("ip1")

    blocked, _ = limiter.check("ip1")
    assert blocked is False


def test_keys_are_independent(clock: FakeClock) -> None:
    """Failures on one key never affect another."""
    limiter = SlidingWindowLimiter(max_failures=1, window_seconds=900, clock=clock)

    limiter.record_failure("ip1")
    blocked, _ = limiter.check("ip2")
    assert blocked is False


def test_bounded_memory_evicts_oldest(clock: FakeClock) -> None:
    """The limiter never tracks more than max_keys entries."""
    limiter = SlidingWindowLimiter(max_failures=1, window_seconds=900, clock=clock, max_keys=3)

    for i in range(10):
        limiter.record_failure(f"ip{i}")

    tracked = sum(1 for k in (f"ip{i}" for i in range(10)) if limiter.check(k)[0])
    assert tracked == 3


async def test_login_blocked_after_five_failures(async_client) -> None:
    """Sixth consecutive failed login returns 429 with Retry-After (T-203)."""
    payload = {"email": "ratelimit@example.com", "password": "WrongPass123"}

    for _ in range(5):
        response = await async_client.post("/auth/login", json=payload)
        assert response.status_code == 401

    response = await async_client.post("/auth/login", json=payload)
    assert response.status_code == 429
    assert "Retry-After" in response.headers
    assert int(response.headers["Retry-After"]) > 0


async def test_login_success_resets_counter(async_client) -> None:
    """Failures before a successful login do not compound afterwards."""
    email = "rl-reset@example.com"

    register = await async_client.post(
        "/auth/register",
        json={"email": email, "password": "GoodPass123", "role": "dog_owner"},
    )
    assert register.status_code == 201

    for _ in range(3):
        failed = await async_client.post(
            "/auth/login", json={"email": "other@example.com", "password": "BadPass123"}
        )
        assert failed.status_code == 401

    ok = await async_client.post("/auth/login", json={"email": email, "password": "GoodPass123"})
    assert ok.status_code == 200

    # Without the reset these would hit the block from the earlier failures.
    for _ in range(5):
        again = await async_client.post(
            "/auth/login", json={"email": "other@example.com", "password": "BadPass123"}
        )
        assert again.status_code == 401, "counter must have been reset by successful login"

    blocked = await async_client.post(
        "/auth/login", json={"email": "other@example.com", "password": "BadPass123"}
    )
    assert blocked.status_code == 429
