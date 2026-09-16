import asyncio
import unittest

from nifc_async_storage import AsyncStoredResearchCoordinator
from nifc_fetch import FetchResult


class Store:
    def __init__(self):
        self.data={'version':1,'wait_seconds':0,'failures':0}
        self.saved=[]
    async def async_load(self): return self.data
    async def async_save(self, data): self.saved.append(data); self.data=data


class AsyncStorageTests(unittest.IsolatedAsyncioTestCase):
    async def test_setup_success_and_restart(self):
        store=Store()
        async def fetch(): return FetchResult((),1,1,'terminal_reported')
        coordinator=AsyncStoredResearchCoordinator(store,fetcher=fetch,clock=lambda:0)
        with self.assertRaises(RuntimeError): await coordinator.refresh(enabled=True)
        await coordinator.setup()
        self.assertEqual(await coordinator.refresh(enabled=True),'retrieved')
        self.assertIsNone(store.saved[0]['wait_seconds'])
        self.assertEqual(store.saved[1]['wait_seconds'],900)
        restarted=AsyncStoredResearchCoordinator(store,fetcher=fetch,clock=lambda:10)
        await restarted.setup()
        self.assertEqual(await restarted.refresh(enabled=True),'skipped')
        self.assertIsNone(coordinator.diagnostics()['problem'])

    async def test_load_failure_is_visible_and_never_initializes(self):
        store=Store(); store.data=None
        coordinator=AsyncStoredResearchCoordinator(store)
        with self.assertRaises(ValueError): await coordinator.setup()
        self.assertEqual(coordinator.diagnostics()['problem'],'storage_load_failed')
        self.assertEqual(store.saved,[])

    async def test_cancelled_write_finishes_before_owner_unlocks(self):
        started,release=asyncio.Event(),asyncio.Event()
        class SlowStore(Store):
            async def async_save(self,data):
                started.set(); await release.wait(); await super().async_save(data)
        async def fetch(): self.fail('Cancelled preflight must not fetch')
        store=SlowStore(); coordinator=AsyncStoredResearchCoordinator(store,fetcher=fetch)
        await coordinator.setup()
        task=asyncio.create_task(coordinator.refresh(enabled=True))
        await started.wait(); task.cancel(); await asyncio.sleep(0)
        self.assertEqual(await coordinator.refresh(enabled=True),'skipped')
        self.assertFalse(task.done())
        release.set()
        with self.assertRaises(asyncio.CancelledError): await task
        self.assertIsNone(store.data['wait_seconds'])
        self.assertFalse(coordinator.diagnostics()['in_flight'])

    async def test_save_failure_retains_prior_response_and_diagnostics(self):
        class BrokenStore(Store):
            async def async_save(self,data): raise OSError('synthetic private path')
        store=BrokenStore(); coordinator=AsyncStoredResearchCoordinator(store)
        await coordinator.setup()
        with self.assertRaises(OSError): await coordinator.refresh(enabled=True)
        self.assertEqual(await coordinator.refresh(enabled=True),'skipped')
        report=coordinator.diagnostics()
        self.assertEqual(report['problem'],'storage_save_failed')
        self.assertNotIn('private',str(report))

    async def test_store_wait_does_not_block_event_loop(self):
        entered,release=asyncio.Event(),asyncio.Event()
        class SlowStore(Store):
            async def async_load(self): entered.set(); await release.wait(); return self.data
        coordinator=AsyncStoredResearchCoordinator(SlowStore())
        task=asyncio.create_task(coordinator.setup())
        await entered.wait()
        self.assertFalse(task.done())
        release.set(); await task
