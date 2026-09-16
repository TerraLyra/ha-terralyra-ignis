"""Explicit persistent research lifecycle, not a Home Assistant coordinator."""
import asyncio
from dataclasses import replace
import math
import time

from nifc_coordinator import ResearchCoordinator
from nifc_refresh import due
from nifc_storage import load_cooldown, save_cooldown


class PersistentResearchCoordinator:
    """One owner per storage directory; file I/O is synchronous and bounded.

    A valid checkpoint must already exist. Initialization is an explicit call to
    save_cooldown with a chosen initial state, never an implicit recovery action.
    File operations must not be run on the HA event loop in future integration.
    """
    def __init__(self, directory, *, clock=time.monotonic, **kwargs):
        self._directory, self._clock = directory, clock
        self._inner = ResearchCoordinator(state=load_cooldown(directory, now=clock()),
                                          clock=clock, **kwargs)
        self._lock = asyncio.Lock()

    @property
    def state(self):
        return self._inner.state

    def _pause(self, previous):
        self._inner.state = replace(previous, next_attempt_at=math.inf,
                                    status='persistence_review_required')

    async def refresh(self, *, enabled=False):
        if not due(self.state, now=self._clock(), enabled=enabled, in_flight=self._lock.locked()):
            return 'skipped'
        async with self._lock:
            previous = self.state
            # An interrupted process must not restart into an immediate retry.
            # This marker deliberately survives cancellation/unexpected failure.
            try:
                save_cooldown(self._directory, replace(previous, next_attempt_at=math.inf),
                              now=self._clock())
            except Exception:
                self._pause(previous)
                raise
            try:
                outcome = await self._inner.refresh(enabled=True)
                save_cooldown(self._directory, self.state, now=self._clock())
            except asyncio.CancelledError:
                self._pause(previous)
                raise
            except Exception:
                self._pause(previous)
                raise
            return outcome
