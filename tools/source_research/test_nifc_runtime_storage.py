import asyncio
import math
import unittest
from dataclasses import replace
from nifc_package import load_module
from test_nifc_async_storage import Store

GuardedStore = load_module('storage').GuardedStore
Stored = load_module('stored_coordinator').NifcStoredCoordinator
checkpoint = load_module('coordinator').checkpoint
restore = load_module('coordinator').restore_checkpoint
RefreshState = load_module('refresh').RefreshState
failed = load_module('refresh').failed


def create_task(coro, name):
    return asyncio.create_task(coro, name=name)


class GuardTests(unittest.IsolatedAsyncioTestCase):
    async def test_timeout_retains_write_and_requires_review(self):
        entered, release = asyncio.Event(), asyncio.Event()
        class SlowStore(Store):
            async def async_save(self, data):
                entered.set(); await release.wait(); await super().async_save(data)
        raw = SlowStore()
        guarded = GuardedStore(raw, create_task, timeout=0.01)
        with self.assertRaises(OSError): await guarded.async_save({'preserve': True})
        self.assertTrue(guarded.pending)
        self.assertTrue(guarded.blocked)
        with self.assertRaises(OSError): guarded.allow_review()
        with self.assertRaises(OSError): await guarded.async_save({'overwrite': True})
        release.set(); await guarded._pending
        self.assertEqual(raw.data, {'preserve': True})
        with self.assertRaises(OSError): await guarded.async_load()
        guarded.allow_review()
        self.assertEqual(await guarded.async_load(), {'preserve': True})

    async def test_cancelled_caller_leaves_observed_write(self):
        entered, release = asyncio.Event(), asyncio.Event()
        class SlowStore(Store):
            async def async_save(self, data):
                entered.set(); await release.wait(); raise OSError('synthetic')
        guarded = GuardedStore(SlowStore(), create_task)
        task = asyncio.create_task(guarded.async_save({}))
        await entered.wait(); task.cancel()
        with self.assertRaises(asyncio.CancelledError): await task
        self.assertTrue(guarded.pending)
        release.set()
        with self.assertRaises(OSError): await guarded._pending
        await asyncio.sleep(0)
        self.assertTrue(guarded.blocked)

    async def test_recovery_preserves_saved_and_live_server_wait(self):
        store = Store()
        state = failed(RefreshState(), now=100, kind='access_denied', server_wait=7200)
        store.data = checkpoint(state, now=100)
        self.assertEqual(store.data['version'], 2)
        coordinator = Stored(store, clock=lambda: 500)
        await coordinator.setup()
        self.assertTrue(math.isinf(coordinator.state.next_attempt_at))
        await coordinator.recover()
        self.assertEqual(coordinator.state.next_attempt_at, 7700)
        self.assertEqual(store.data['wait_seconds'], 7200)

    async def test_unknown_unbounded_or_corrupt_pause_is_not_reset(self):
        for saved in ({'version':1,'wait_seconds':None,'failures':1}, None, {'bad':True}):
            store=Store();store.data=saved;coordinator=Stored(store)
            with self.assertRaises(ValueError):await coordinator.recover()
            self.assertEqual(store.saved,[])
        state=failed(RefreshState(),now=0,kind='rate_limited',server_wait=math.inf)
        self.assertIsNone(state.resume_after_review_at)
        self.assertEqual(checkpoint(state,now=0)['version'],1)

    async def test_recovery_keeps_response_and_never_fetches(self):
        query=load_module('query')
        async def fetch():return query.FetchResult((),1,1,'terminal_reported')
        store=Store();coordinator=Stored(store,fetcher=fetch,clock=lambda:0)
        await coordinator.setup();await coordinator.refresh(enabled=True)
        cached=coordinator.state.last_success
        await coordinator.recover()
        self.assertIs(coordinator.state.last_success,cached)
        self.assertEqual(coordinator.state.next_attempt_at,900)

    def test_recovery_checkpoint_rejects_invalid_versions_and_bounds(self):
        for data in ({'version':2,'wait_seconds':0,'failures':0,'resume_wait_seconds':1},
                     {'version':2,'wait_seconds':None,'failures':0,'resume_wait_seconds':True}):
            with self.assertRaises(ValueError):restore(data,now=0)
