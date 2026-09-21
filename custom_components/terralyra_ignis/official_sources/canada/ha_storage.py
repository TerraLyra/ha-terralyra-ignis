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

    def __init__(self, store, *, timeout=30, create_task=None):
        self.store = store
        self.blocked = False
        self._lock = asyncio.Lock()
        self.timeout = timeout
        self.create_task = create_task or (lambda coro, name: asyncio.create_task(coro, name=name))
        self._pending = None
        self.problem = None

    @property
    def pending(self):
        return self._pending is not None and not self._pending.done()

    def _finished(self, task):
        # Retrieve late failures even after a timeout has returned to the caller.
        if task.cancelled() or task.exception() is not None:
            self.blocked = True
            self.problem = 'storage_failed'

    async def _run(self, method, *args):
        if self.blocked or self.pending:
            raise OSError('Storage requires review')
        task = self.create_task(method(*args), 'Canada storage')
        self._pending = task
        task.add_done_callback(self._finished)
        try:
            done, _ = await asyncio.wait({task}, timeout=self.timeout)
            if not done:
                self.problem = 'storage_timeout'
                raise OSError('Storage operation timed out')
            return task.result()
        except BaseException:
            self.blocked = True
            if self.problem is None:
                self.problem = 'storage_interrupted'
            raise

    async def async_initialize(self, *, confirmed_new=False):
        if confirmed_new is not True:
            raise ValueError('Explicit first-use confirmation required')
        async with self._lock:
            if self.blocked:
                raise OSError('Storage requires review')
            try:
                existing = await self._run(self.store.async_load)
                if existing is not None:
                    state = self._decode(existing)
                    if state.review_required:
                        raise ValueError('Existing state requires review')
                    return 'existing'
                await self._run(self.store.async_save, json.loads(encode(RefreshState())))
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
                data = await self._run(self.store.async_load)
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
                await self._run(self.store.async_save, json.loads(encode(state)))
            except BaseException:
                self.blocked = True
                raise
