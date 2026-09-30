"""Shared request pacing for future location forecast clients; opt-in only."""
from __future__ import annotations

import asyncio
import math
import time
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from typing import TypeVar

from .products.fire_risk import (
    FireRiskError, FireRiskRateLimitError, FireRiskServiceUnavailableError,
    FireRiskTemporaryServiceError,
)

_T = TypeVar("_T")


class ForecastRequestDeferred(FireRiskError):
    """Local scheduling deferral, not a new upstream request failure."""

    def __init__(self, retry_after: timedelta) -> None:
        super().__init__("Forecast requests are temporarily deferred")
        self.retry_after = retry_after


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
        utcnow: Callable[[], datetime] = lambda: datetime.now(UTC),
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
        self._utcnow = utcnow
        self._cooldown_until = 0.0
        self._lock = asyncio.Lock()
        self._next_request = 0.0

    async def run(self, operation: Callable[[], Awaitable[_T]]) -> _T:
        """Run at most one operation, preserving cancellation and error types."""
        async with self._lock:
            if (remaining := self._cooldown_until - self._clock()) > 0:
                raise ForecastRequestDeferred(timedelta(seconds=remaining))
            while (delay := self._next_request - self._clock()) > 0:
                await self._sleep(delay)
            try:
                return await operation()
            except (FireRiskRateLimitError, FireRiskServiceUnavailableError,
                    FireRiskTemporaryServiceError) as err:
                retry = getattr(err, "retry_after", None)
                # Bound remote advice; apply a default pause even without it.
                delay = max(15 * 60, min(60 * 60, retry.total_seconds())) if retry else 15 * 60
                self._cooldown_until = max(self._cooldown_until, self._clock() + delay)
                raise
            finally:
                self._next_request = max(self._next_request, self._clock() + self._spacing)

    def export_cooldown(self) -> dict[str, int | str] | None:
        """Return a bounded UTC deadline for the owning service to persist."""
        remaining = self._cooldown_until - self._clock()
        if remaining <= 0:
            return None
        return {"schema": 1, "until": (
            self._utcnow() + timedelta(seconds=min(remaining, 3600))
        ).isoformat()}

    def import_cooldown(self, payload: object) -> bool:
        """Restore into this process's monotonic clock, never clear a later pause."""
        try:
            if (not isinstance(payload, dict) or type(payload.get("schema")) is not int
                    or payload["schema"] != 1 or not isinstance(payload.get("until"), str)):
                return False
            until = datetime.fromisoformat(payload["until"])
            if until.tzinfo is None or until.utcoffset() is None:
                return False
            remaining = (until - self._utcnow()).total_seconds()
            if not 0 < remaining <= 3600:
                return False
        except (ValueError, TypeError, OverflowError):
            return False
        self._cooldown_until = max(self._cooldown_until, self._clock() + remaining)
        return True
