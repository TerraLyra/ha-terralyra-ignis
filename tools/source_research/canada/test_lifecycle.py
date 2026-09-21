import asyncio
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock
from controller import Controller
from lifecycle import Lifecycle

EMPTY = ({'type': 'FeatureCollection', 'features': [],
          'numberMatched': 0, 'numberReturned': 0}, {})


class LifecycleTests(unittest.IsolatedAsyncioTestCase):
    async def test_default_disabled_and_no_places_never_fetch(self):
        owner = AsyncMock()
        lifecycle = Lifecycle(owner)
        self.assertIsNone(lifecycle.attach('entry'))
        self.assertIsNone(lifecycle.attach('entry', enabled=True))
        self.assertIsNone(lifecycle.request_refresh())
        owner.refresh.assert_not_awaited()
        await lifecycle.stop()

    async def test_shared_task_and_remaining_consumer(self):
        entered, release = asyncio.Event(), asyncio.Event()
        async def refresh():
            entered.set()
            await release.wait()
            return 'state'
        owner = AsyncMock()
        owner.refresh.side_effect = refresh
        lifecycle = Lifecycle(owner)
        first = lifecycle.attach('one', enabled=True, has_locations=True)
        second = lifecycle.attach('two', enabled=True, has_locations=True)
        self.assertIs(first, second)
        await entered.wait()
        await lifecycle.detach('one')
        self.assertFalse(first.done())
        release.set()
        await first
        self.assertEqual(lifecycle.last_state, 'state')
        owner.refresh.assert_awaited_once()
        await lifecycle.stop()

    async def test_stop_during_fetch_and_restart_preserves_pause(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'state.json'
            entered = asyncio.Event()
            async def fetch(session):
                entered.set()
                await asyncio.Event().wait()
            clock = lambda: datetime(2026, 9, 21, tzinfo=UTC)
            lifecycle = Lifecycle(Controller(path, None, clock=clock, fetcher=fetch))
            task = lifecycle.attach('one', enabled=True, has_locations=True)
            await entered.wait()
            await lifecycle.stop()
            self.assertTrue(task.cancelled())
            with self.assertRaises(RuntimeError):
                lifecycle.attach('one', enabled=True, has_locations=True)
            next_fetch = AsyncMock(return_value=EMPTY)
            restarted = Lifecycle(Controller(path, None, clock=clock, fetcher=next_fetch))
            await restarted.attach('one', enabled=True, has_locations=True)
            next_fetch.assert_not_awaited()
            await restarted.stop()

    async def test_disk_error_keeps_cached_state_without_raw_error(self):
        owner = AsyncMock()
        owner.refresh.side_effect = ['cached', OSError('private path')]
        lifecycle = Lifecycle(owner)
        await lifecycle.attach('one', enabled=True, has_locations=True)
        await lifecycle.request_refresh()
        self.assertEqual(lifecycle.last_state, 'cached')
        self.assertEqual(lifecycle.problem, 'refresh_failed')
        await lifecycle.stop()

    async def test_repeated_stop_waits_for_cleanup_without_recancelling(self):
        entered, cleaning, release = asyncio.Event(), asyncio.Event(), asyncio.Event()
        async def refresh():
            entered.set()
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                cleaning.set()
                await release.wait()
                raise
        owner = AsyncMock()
        owner.refresh.side_effect = refresh
        lifecycle = Lifecycle(owner)
        task = lifecycle.attach('one', enabled=True, has_locations=True)
        await entered.wait()
        first = asyncio.create_task(lifecycle.stop())
        await cleaning.wait()
        second = asyncio.create_task(lifecycle.stop())
        await asyncio.sleep(0)
        self.assertFalse(first.done())
        self.assertFalse(second.done())
        self.assertEqual(task.cancelling(), 1)
        release.set()
        await asyncio.gather(first, second)
        self.assertTrue(task.cancelled())
