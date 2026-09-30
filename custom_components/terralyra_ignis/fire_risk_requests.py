"""Shared request pacing for future location forecast clients; opt-in only."""
from __future__ import annotations

import asyncio
import math
import time
from collections.abc import Awaitable, Callable
from typing import TypeVar

from .products.fire_risk import (
    FireRiskRateLimitError, FireRiskServiceUnavailableError,
    FireRiskTemporaryServiceError,
)

_T = TypeVar("_T")


class ForecastRequestGate:
    """Serialize/pause requests within one installation and provider.

    This is an internal conservative pacing policy, not a publisher rate limit.
    Share one instance across all clients for that provider. The gate does not
    retry failed operations and is not yet connected to runtime retrieval.
    """

    def __init__(
        self, *, spacing_seconds: float = 1.0,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        if (
            isinstance(spacing_seconds, bool)
            or not math.isfinite(spacing_seconds)
            or not 1 <= spacing_seconds <= 60
        ):
            raise ValueError("Invalid forecast request spacing")
        self._spacing = spacing_seconds
        self._clock = clock
        self._sleep = sleep
        self._lock = asyncio.Lock()
        self._next_request = 0.0

    async def run(self, operation: Callable[[], Awaitable[_T]]) -> _T:
        """Run at most one operation, preserving cancellation and error types."""
        async with self._lock:
            while (delay := self._next_request - self._clock()) > 0:
                await self._sleep(delay)
            try:
                return await operation()
            except (FireRiskRateLimitError, FireRiskServiceUnavailableError,
                    FireRiskTemporaryServiceError) as err:
                retry = getattr(err, "retry_after", None)
                # Bound remote advice; apply a default pause even without it.
                delay = max(15 * 60, min(60 * 60, retry.total_seconds())) if retry else 15 * 60
                self._next_request = max(self._next_request, self._clock() + delay)
                raise
            finally:
                self._next_request = max(self._next_request, self._clock() + self._spacing)
