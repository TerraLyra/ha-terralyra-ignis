"""Bounded storage waits while retaining ownership of uncancellable writes."""
import asyncio


class GuardedStore:
    """A timeout never cancels a disk write or permits an overlapping operation.

    HA tracks background tasks for shutdown. This wrapper also retains a strong
    reference and retrieves every result, even after its waiting caller has left.
    A timed-out/cancelled operation latches a review requirement until explicit
    recovery. No method deletes or replaces storage files.
    """
    def __init__(self, store, create_task, *, timeout=30):
        self._store, self._create_task, self._timeout = store, create_task, timeout
        self._pending = None
        self._blocked = False

    @property
    def pending(self):
        return self._pending is not None and not self._pending.done()

    @property
    def blocked(self):
        return self._blocked

    def allow_review(self):
        if self.pending:
            raise OSError('Storage operation still pending')
        self._blocked = False

    def _done(self, task):
        if task.cancelled():
            self._blocked = True
        elif task.exception() is not None:
            self._blocked = True

    async def _run(self, method, *args):
        if self.pending or self._blocked:
            raise OSError('Storage requires review')
        task = self._create_task(method(*args), 'NIFC storage')
        self._pending = task
        task.add_done_callback(self._done)
        try:
            done, _ = await asyncio.wait({task}, timeout=self._timeout)
            if not done:
                raise OSError('Storage operation timed out; review required')
            return task.result()
        except BaseException:
            self._blocked = True
            raise

    async def async_load(self):
        return await self._run(self._store.async_load)

    async def async_save(self, data):
        return await self._run(self._store.async_save, data)
