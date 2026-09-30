"""Shared pacing without real network traffic or wall-clock sleeps."""
import asyncio
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from custom_components.terralyra_ignis.fire_risk_requests import ForecastRequestDeferred, ForecastRequestGate
from custom_components.terralyra_ignis.products.fire_risk import FireRiskRateLimitError


class Clock:
    def __init__(self):
        self.now = 0.0
        self.waits = []

    def read(self):
        return self.now

    async def sleep(self, delay):
        self.waits.append(delay)
        self.now += delay


@pytest.mark.parametrize("spacing", [0, -1, 61, True, float("nan"), float("inf")])
def test_invalid_spacing(spacing):
    with pytest.raises(ValueError):
        ForecastRequestGate(spacing_seconds=spacing)


async def test_shared_gate_spaces_requests():
    clock = Clock()
    gate = ForecastRequestGate(clock=clock.read, sleep=clock.sleep)
    operation = AsyncMock(return_value="result")
    assert await gate.run(operation) == "result"
    assert await gate.run(operation) == "result"
    assert clock.waits == [1.0]
    assert operation.await_count == 2


@pytest.mark.parametrize(("retry", "expected"), [(None, 900), (30, 900), (1800, 1800), (7200, 3600)])
async def test_rate_limit_pauses_peers_without_retrying(retry, expected):
    clock = Clock()
    gate = ForecastRequestGate(clock=clock.read, sleep=clock.sleep)
    error = FireRiskRateLimitError("limited", 429, timedelta(seconds=retry) if retry else None)
    failing = AsyncMock(side_effect=error)
    with pytest.raises(FireRiskRateLimitError) as exc:
        await gate.run(failing)
    assert exc.value is error
    failing.assert_awaited_once()
    peer = AsyncMock(return_value=42)
    with pytest.raises(ForecastRequestDeferred) as deferred:
        await gate.run(peer)
    assert deferred.value.retry_after.total_seconds() == expected
    peer.assert_not_awaited()
    assert clock.waits == []
    clock.now += expected
    assert await gate.run(peer) == 42


async def test_concurrent_requests_are_serialized():
    clock = Clock()
    gate = ForecastRequestGate(clock=clock.read, sleep=clock.sleep)
    started, finish = asyncio.Event(), asyncio.Event()
    calls = []

    async def first():
        calls.append("first-start")
        started.set()
        await finish.wait()
        calls.append("first-end")

    async def second():
        calls.append("second")

    first_task = asyncio.create_task(gate.run(first))
    await started.wait()
    second_task = asyncio.create_task(gate.run(second))
    finish.set()
    await asyncio.gather(first_task, second_task)
    assert calls == ["first-start", "first-end", "second"]
    assert clock.waits == [1.0]


async def test_cancellation_releases_gate_and_preserves_pause():
    clock = Clock()
    gate = ForecastRequestGate(clock=clock.read, sleep=clock.sleep)
    operation = AsyncMock(side_effect=asyncio.CancelledError)
    with pytest.raises(asyncio.CancelledError):
        await gate.run(operation)
    assert await gate.run(AsyncMock(return_value="next")) == "next"
    assert clock.waits == [1.0]


async def test_cooldown_round_trip_across_monotonic_clock_reset():
    clock = Clock()
    now = datetime(2026, 9, 30, tzinfo=UTC)
    gate = ForecastRequestGate(clock=clock.read, sleep=clock.sleep, utcnow=lambda: now)
    with pytest.raises(FireRiskRateLimitError):
        await gate.run(AsyncMock(side_effect=FireRiskRateLimitError("limit", 429)))
    saved = gate.export_cooldown()
    restarted = ForecastRequestGate(clock=lambda: 100.0, utcnow=lambda: now + timedelta(seconds=100))
    assert restarted.import_cooldown(saved)
    with pytest.raises(ForecastRequestDeferred) as exc:
        await restarted.run(AsyncMock())
    assert exc.value.retry_after.total_seconds() == 800


@pytest.mark.parametrize("until", ["invalid", "2026-09-30T00:10:00",
    "2026-09-29T00:10:00+00:00", "2026-10-30T00:10:00+00:00"])
def test_cooldown_restore_rejects_unsafe_deadlines(until):
    gate = ForecastRequestGate(utcnow=lambda: datetime(2026, 9, 30, tzinfo=UTC))
    assert not gate.import_cooldown({"schema": 1, "until": until})
    assert gate.export_cooldown() is None
