"""Shared pacing without real network traffic or wall-clock sleeps."""
import asyncio
from datetime import timedelta
from unittest.mock import AsyncMock

import pytest

from custom_components.terralyra_ignis.fire_risk_requests import ForecastRequestGate
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
    assert await gate.run(AsyncMock(return_value=42)) == 42
    assert clock.waits == [expected]


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
