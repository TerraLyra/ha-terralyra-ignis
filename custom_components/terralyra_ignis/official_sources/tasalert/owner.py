"""Serialized HA Store/session adapter, inert until explicitly initialized/refreshed."""
import asyncio
import json
from .engine import Engine
from .engine_storage import decode, encode
from .async_fetch import fetch_once

STORE_KEY = 'terralyra_ignis_tasalert_v1'


class TasAlertOwner:
    def __init__(self, store, session, *, fetcher=fetch_once):
        self.store=store
        self.session=session
        self.fetcher=fetcher
        self.state=None
        self.blocked=False
        self._lock=asyncio.Lock()

    async def async_load(self, *, confirmed_new=False):
        async with self._lock:
            if self.blocked:raise OSError('TasALERT storage requires review')
            try:
                data=await self.store.async_load()
                if data is None:
                    if not confirmed_new:raise ValueError('TasALERT storage not initialized')
                    state=Engine()
                    await self.store.async_save(json.loads(encode(state)))
                else:
                    state=decode(json.dumps(data,allow_nan=False).encode())
                self.state=state
            except BaseException:
                self.blocked=True
                raise

    async def async_refresh(self):
        async with self._lock:
            if self.blocked or self.state is None:raise OSError('TasALERT storage is not ready')
            from aiohttp import ClientError
            candidate=await self.fetcher(self.state,self.session,transport_errors=(ClientError,OSError))
            if candidate is self.state:return self.state
            # A cancelled/failed save has unknown durability: block subsequent I/O.
            try:
                await self.store.async_save(json.loads(encode(candidate)))
            except BaseException:
                self.blocked=True
                raise
            self.state=candidate
            return self.state


def create_owner(hass):
    """Construct only; no load, request, scheduler, entities or registry changes."""
    from homeassistant.helpers.aiohttp_client import async_get_clientsession
    from homeassistant.helpers.storage import Store
    return TasAlertOwner(Store(hass,1,STORE_KEY),async_get_clientsession(hass))
