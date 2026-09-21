"""Explicit Canada HA persistence; missing established state never fetches."""
import asyncio
import json

from .retry import RefreshState
from .storage import decode, encode


class CanadaStore:
    """Adapt HA Store without touching any incident history or other providers.

    Construction is inert. Initialization is explicit and never replaces an
    existing record. A disk failure latches a block for this owner lifetime.
    Controller owns and shields save completion before releasing its lock.
    """

    def __init__(self, store):
        self.store = store
        self.blocked = False
        self._lock = asyncio.Lock()

    async def async_initialize(self, *, confirmed_new=False):
        if confirmed_new is not True:
            raise ValueError('Explicit first-use confirmation required')
        async with self._lock:
            if self.blocked:
                raise OSError('Storage requires review')
            try:
                existing = await self.store.async_load()
                if existing is not None:
                    state = self._decode(existing)
                    if state.review_required:
                        raise ValueError('Existing state requires review')
                    return 'existing'
                await self.store.async_save(json.loads(encode(RefreshState())))
                return 'initialized'
            except BaseException:
                self.blocked = True
                raise

    @staticmethod
    def _decode(data):
        return decode(json.dumps(data, allow_nan=False).encode())

    async def async_load(self):
        async with self._lock:
            if self.blocked:
                raise OSError('Storage requires review')
            try:
                data = await self.store.async_load()
                if data is None:
                    raise ValueError('Canada state is not initialized or is missing')
                state = self._decode(data)
                if state.status == 'storage_error':
                    self.blocked = True
                return state
            except BaseException:
                self.blocked = True
                raise

    async def async_save(self, state):
        async with self._lock:
            if self.blocked:
                raise OSError('Storage requires review')
            try:
                await self.store.async_save(json.loads(encode(state)))
            except BaseException:
                self.blocked = True
                raise
