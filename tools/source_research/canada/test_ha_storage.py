import asyncio
import copy
import unittest
from datetime import UTC, datetime
from unittest.mock import AsyncMock
from canada_package import load_module
from controller import Controller
from retry import RefreshState

CanadaStore = load_module('ha_storage').CanadaStore
EMPTY = ({'type': 'FeatureCollection', 'features': [], 'numberMatched': 0,
          'numberReturned': 0}, {})


class MemoryStore:
    def __init__(self):
        self.data = None
        self.writes = 0

    async def async_load(self):
        return copy.deepcopy(self.data)

    async def async_save(self, data):
        self.data = copy.deepcopy(data)
        self.writes += 1


class HAStorageTests(unittest.IsolatedAsyncioTestCase):
    def owner(self, store, fetcher):
        return Controller(None, None, store=store, fetcher=fetcher,
                          clock=lambda: datetime(2026, 9, 22, tzinfo=UTC))

    async def test_missing_store_blocks_fetch_and_implicit_initialization(self):
        disk = MemoryStore()
        store = CanadaStore(disk)
        fetcher = AsyncMock(return_value=EMPTY)
        with self.assertRaises(ValueError):
            await self.owner(store, fetcher).refresh()
        fetcher.assert_not_awaited()
        self.assertEqual(disk.writes, 0)
        with self.assertRaises(OSError):
            await store.async_initialize(confirmed_new=True)

    async def test_explicit_initialization_and_restart_preserve_cooldown(self):
        disk = MemoryStore()
        store = CanadaStore(disk)
        with self.assertRaises(ValueError):
            await store.async_initialize()
        self.assertEqual(await store.async_initialize(confirmed_new=True), 'initialized')
        fetcher = AsyncMock(return_value=EMPTY)
        state = await self.owner(store, fetcher).refresh()
        saved = copy.deepcopy(disk.data)
        restarted = CanadaStore(disk)
        self.assertEqual(await restarted.async_initialize(confirmed_new=True), 'existing')
        restored = await self.owner(restarted, fetcher).refresh()
        self.assertEqual(restored.next_attempt, state.next_attempt)
        self.assertEqual(disk.data, saved)
        fetcher.assert_awaited_once()

    async def test_corrupt_store_is_preserved_and_never_fetched(self):
        disk = MemoryStore()
        disk.data = {'version': 999}
        store = CanadaStore(disk)
        fetcher = AsyncMock()
        state = await self.owner(store, fetcher).refresh()
        self.assertEqual(state.status, 'storage_error')
        self.assertTrue(store.blocked)
        fetcher.assert_not_awaited()
        self.assertEqual(disk.data, {'version': 999})
        self.assertEqual(disk.writes, 0)

    async def test_reservation_failure_blocks_network_and_future_saves(self):
        disk = MemoryStore()
        store = CanadaStore(disk)
        await store.async_initialize(confirmed_new=True)
        disk.async_save = AsyncMock(side_effect=OSError('disk unavailable'))
        fetcher = AsyncMock()
        with self.assertRaises(OSError):
            await self.owner(store, fetcher).refresh()
        fetcher.assert_not_awaited()
        with self.assertRaises(OSError):
            await store.async_save(RefreshState())
        disk.async_save.assert_awaited_once()

    async def test_cancelled_reservation_finishes_before_owner_unlocks(self):
        disk = MemoryStore()
        store = CanadaStore(disk)
        await store.async_initialize(confirmed_new=True)
        entered, release = asyncio.Event(), asyncio.Event()
        original_save = disk.async_save
        async def delayed_save(data):
            entered.set()
            await release.wait()
            await original_save(data)
        disk.async_save = delayed_save
        fetcher = AsyncMock()
        owner = self.owner(store, fetcher)
        task = asyncio.create_task(owner.refresh())
        await entered.wait()
        task.cancel()
        await asyncio.sleep(0)
        self.assertTrue(owner.lock.locked())
        release.set()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertFalse(owner.lock.locked())
        await self.owner(CanadaStore(disk), fetcher).refresh()
        fetcher.assert_not_awaited()
