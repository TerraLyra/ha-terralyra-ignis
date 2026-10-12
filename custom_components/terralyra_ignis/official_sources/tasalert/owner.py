"""Serialized HA Store/session adapter, inert until explicitly initialized/refreshed."""
import asyncio
import json
from .engine import Engine
from .engine_storage import decode, encode
from .async_fetch import fetch_once

STORE_KEY = 'terralyra_ignis_tasalert_v1'


class TasAlertOwner:
    def __init__(self, store, session, *, fetcher=fetch_once, storage_timeout=30):
        self.store=store
        self.session=session
        self.fetcher=fetcher
        self.state=None
        self.blocked=False
        self._lock=asyncio.Lock()
        self.closed=False
        self.storage_timeout=storage_timeout
        self._pending=None
        self._active=None

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
                    if not confirmed_new:raise ValueError('TasALERT storage not initialized')
                    state=Engine()
                    await self._storage(self.store.async_save,json.loads(encode(state)))
                else:
                    state=decode(json.dumps(data,allow_nan=False).encode())
                if self.closed:raise OSError("TasALERT owner closed")
                self.state=state
            except BaseException:
                self.blocked=True
                raise

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
