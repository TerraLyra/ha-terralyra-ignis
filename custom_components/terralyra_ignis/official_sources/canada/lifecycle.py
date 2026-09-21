"""Experimental lifecycle boundary; no HA registration or automatic scheduler."""
import asyncio


class Lifecycle:
    """Own at most one refresh task across explicitly enabled consumers.

    HA can call request_refresh from its timer later. The controller retains
    disk ownership until cancellation cleanup finishes. A stopping instance
    cannot be reactivated; a new instance must reuse the persisted controller.
    """

    def __init__(self, controller):
        self.controller = controller
        self.consumers = set()
        self.task = None
        self.stopping = False
        self.last_state = None
        self.problem = None

    def attach(self, consumer, *, enabled=False, has_locations=False):
        if type(enabled) is not bool or type(has_locations) is not bool:
            raise ValueError('Explicit eligibility required')
        if self.stopping:
            raise RuntimeError('Lifecycle is stopping')
        if enabled and has_locations:
            self.consumers.add(consumer)
        else:
            self.consumers.discard(consumer)
        return self.request_refresh()

    def request_refresh(self):
        if self.stopping or not self.consumers:
            if (self.task is not None and not self.task.done()
                    and not self.task.cancelling()):
                self.task.cancel()
            return None
        if self.task is None or self.task.done():
            self.task = asyncio.create_task(self._run())
        return self.task

    async def _run(self):
        try:
            self.last_state = await self.controller.refresh()
            self.problem = None
        except (OSError, ValueError):
            # Keep cached state; raw source/disk error text is not presentation.
            self.problem = 'refresh_failed'

    async def detach(self, consumer):
        self.consumers.discard(consumer)
        if not self.consumers:
            await self._cancel()

    async def stop(self):
        self.stopping = True
        self.consumers.clear()
        await self._cancel()

    async def _cancel(self):
        task = self.task
        if task is not None and not task.done():
            if not task.cancelling():
                task.cancel()
            # Shield cancellation cleanup, especially the controller's disk write.
            try:
                await asyncio.shield(task)
            except asyncio.CancelledError:
                if not task.done():
                    await task
                    raise
