"""NIFC lifecycle with an injected asynchronous store interface."""
import asyncio
from dataclasses import replace
import math
import time

from .coordinator import NifcCoordinator, checkpoint, restore_checkpoint
from .refresh import due


async def _settled_save(store, payload):
    """Do not release ownership while a cancelled caller's write is still running."""
    task = asyncio.create_task(store.async_save(payload))
    cancelled = False
    while not task.done():
        try:
            await asyncio.shield(task)
        except asyncio.CancelledError:
            cancelled = True
    task.result()
    if cancelled:
        raise asyncio.CancelledError


class NifcStoredCoordinator:
    """One instance/store owner; explicit setup and refresh, no scheduler or HA import.

    Store must provide async_load/async_save without blocking the event loop.
    Cancellation waits for an in-progress save to settle; a hung store can therefore
    delay cancellation. Production storage timeout/recovery remains a separate gate.
    """
    def __init__(self, store, *, clock=time.monotonic, **kwargs):
        self._store, self._clock, self._kwargs = store, clock, kwargs
        self._inner = None
        self._lock = asyncio.Lock()
        self._problem = 'not_loaded'

    async def setup(self):
        async with self._lock:
            if self._inner is not None:
                return
            try:
                data = await self._store.async_load()
                state = restore_checkpoint(data, now=self._clock())
            except Exception:
                self._problem = 'storage_load_failed'
                raise
            self._inner = NifcCoordinator(state=state, clock=self._clock, **self._kwargs)
            self._problem = 'review_required' if math.isinf(state.next_attempt_at) else None

    @property
    def state(self):
        return None if self._inner is None else self._inner.state

    def diagnostics(self):
        state = self.state
        return {'problem': self._problem, 'in_flight': self._lock.locked(),
                'has_last_response': state is not None and state.last_success is not None,
                'failures': 0 if state is None else state.failures,
                'source_freshness': 'not_established'}

    async def refresh(self, *, enabled=False):
        if self._inner is None:
            raise RuntimeError('Explicit successful setup required')
        if not due(self.state, now=self._clock(), enabled=enabled, in_flight=self._lock.locked()):
            return 'skipped'
        async with self._lock:
            previous = self.state
            stage = 'storage_save_failed'
            try:
                await _settled_save(self._store, checkpoint(
                    replace(previous, next_attempt_at=math.inf), now=self._clock()))
                stage = 'request_failed'
                outcome = await self._inner.refresh(enabled=True)
                stage = 'storage_save_failed'
                await _settled_save(self._store, checkpoint(self.state, now=self._clock()))
            except (Exception, asyncio.CancelledError):
                self._inner.state = replace(previous, next_attempt_at=math.inf,
                                            status='persistence_review_required')
                self._problem = stage
                raise
            self._problem = None if outcome == 'retrieved' else self.state.status
            return outcome
