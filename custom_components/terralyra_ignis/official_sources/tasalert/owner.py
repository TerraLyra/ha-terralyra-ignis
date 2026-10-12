"""Serialized HA Store/session adapter, inert until explicitly initialized/refreshed."""
import asyncio
import json
from .engine import Engine
from .engine_storage import decode, encode
from .async_fetch import fetch_once

class InitializationRequired(ValueError):
    """Missing store requires explicit first-use intent, not a reset."""


STORE_KEY = 'terralyra_ignis_tasalert_v1'


class TasAlertOwner:
    def __init__(self, store, session, *, fetcher=fetch_once, storage_timeout=30):
        self.store=store
        self.session=session
        self.fetcher=fetcher
        self.state=None
        self.blocked=False
        self.initialization_required=False
        self._lock=asyncio.Lock()
        self.closed=False
        self.storage_timeout=storage_timeout
        self._pending=None
        self._active=None
        self._recovery_deadline=None

    def diagnostics(self):
        state = self.state
        return {
            'response_status': ('review_required' if self.blocked else
                                'initialization_required' if self.initialization_required else
                                state.response.status if state else 'not_requested'),
            'next_attempt': state.response.next_attempt.isoformat() if state and state.response.next_attempt else None,
            'retained_record_count': len(state.ledger) if state else None,
            'review_record_count': len(state.review) if state else None,
            'source_freshness': 'not_established',
            'attribution': 'TasALERT',
            'license_url': 'https://creativecommons.org/licenses/by/4.0/',
        }

    async def _storage(self, method, *args):
        task=asyncio.create_task(method(*args))
        self._pending=task
        # Observe errors even if a timeout/cancellation ends the caller first.
        task.add_done_callback(lambda done: None if done.cancelled() else done.exception())
        try:
            done,_=await asyncio.wait({task},timeout=self.storage_timeout)
            if not done:raise OSError('TasALERT storage timed out')
            return task.result()
        except BaseException:
            self.blocked=True
            raise

    async def async_close(self):
        self.closed=True
        task=self._active
        if task is not None and task is not asyncio.current_task() and not task.done():
            task.cancel()
            await asyncio.gather(task,return_exceptions=True)
        # The HA session is shared. Never close it here. Pending disk I/O may
        # finish later, but this closed owner cannot fetch or publish new state.


    async def async_load(self, *, confirmed_new=False):
        async with self._lock:
            if self.blocked or self.closed:raise OSError('TasALERT storage requires review')
            try:
                data=await self._storage(self.store.async_load)
                if data is None:
                    if not confirmed_new:
                        self.initialization_required=True
                        raise InitializationRequired('TasALERT storage not initialized')
                    state=Engine()
                    await self._storage(self.store.async_save,json.loads(encode(state)))
                else:
                    state=decode(json.dumps(data,allow_nan=False).encode())
                if self.closed:raise OSError("TasALERT owner closed")
                self.state=state
                self.initialization_required=False
            except InitializationRequired:
                raise
            except BaseException:
                self.blocked=True
                raise

    async def async_recover(self):
        """Re-read a valid durable store after review, never create or reset it."""
        from dataclasses import replace
        from datetime import datetime, UTC
        from .policy import INTERVAL
        async with self._lock:
            if self.closed or (self._pending is not None and not self._pending.done()):
                raise OSError('TasALERT storage operation still pending or owner closed')
            self.blocked = True
            data = await self._storage(self.store.async_load)
            if data is None:
                raise ValueError('Recovery requires an existing valid TasALERT store')
            state = decode(json.dumps(data, allow_nan=False).encode())
            # Unknown durability must not shorten a persisted wait or cause an
            # immediate repeat request after a failed save.
            deadline = max(filter(None, (state.response.next_attempt,
                           self.state.response.next_attempt if self.state else None,
                           self._recovery_deadline,
                           datetime.now(UTC) + INTERVAL)))
            state = replace(state, response=replace(state.response, next_attempt=deadline))
            await self._storage(self.store.async_save, json.loads(encode(state)))
            if self.closed:
                raise OSError('TasALERT owner closed')
            self.state = state
            self.initialization_required = False
            self.blocked = False

    async def async_refresh(self):
        async with self._lock:
            self._active=asyncio.current_task()
            try:
                return await self._refresh_locked()
            finally:
                self._active=None

    async def _refresh_locked(self):
        if self.blocked or self.closed or self.state is None:raise OSError('TasALERT storage is not ready')
        from aiohttp import ClientError
        candidate=await self.fetcher(self.state,self.session,transport_errors=(ClientError,OSError))
        if self.closed:raise OSError('TasALERT owner closed')
        if candidate is self.state:return self.state
        # Preserve a newly received Retry-After even if its disk save fails.
        self._recovery_deadline=candidate.response.next_attempt
        # A cancelled/failed save has unknown durability: block subsequent I/O.
        try:
            await self._storage(self.store.async_save,json.loads(encode(candidate)))
        except BaseException:
            self.blocked=True
            raise
        if self.closed:raise OSError('TasALERT owner closed')
        self.state=candidate
        return self.state

def create_owner(hass):
    """Construct only; no load, request, scheduler, entities or registry changes."""
    from homeassistant.helpers.aiohttp_client import async_get_clientsession
    from homeassistant.helpers.storage import Store
    return TasAlertOwner(Store(hass,1,STORE_KEY),async_get_clientsession(hass))
