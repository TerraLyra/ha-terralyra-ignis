import asyncio
from copy import deepcopy
from datetime import datetime, UTC
import unittest
import importlib.util
from tasalert_package import load
from tasalert_engine import Engine, advance
from test_tasalert_snapshot import record

Owner=load('owner').TasAlertOwner


class Store:
    def __init__(self):self.data=None;self.fail=False;self.saves=0
    async def async_load(self):return deepcopy(self.data)
    async def async_save(self,data):
        if self.fail:raise OSError('disk failed')
        self.saves+=1;self.data=deepcopy(data)


class OwnerTests(unittest.IsolatedAsyncioTestCase):
    async def test_initialization_is_explicit_and_restart_restores(self):
        store=Store();owner=Owner(store,None)
        self.assertEqual(store.saves,0)
        await owner.async_load(confirmed_new=True)
        restored=Owner(store,None);await restored.async_load()
        self.assertEqual(restored.state,Engine())

    async def test_missing_state_blocks_without_fetch(self):
        owner=Owner(Store(),None)
        with self.assertRaises(ValueError):await owner.async_load()
        with self.assertRaises(OSError):await owner.async_refresh()

    @unittest.skipIf(importlib.util.find_spec("aiohttp") is None, "Optional aiohttp unavailable")
    async def test_concurrent_refresh_is_serial_and_failed_save_blocks(self):
        calls=[]
        async def fetch(state,session,**kwargs):
            calls.append(state)
            await asyncio.sleep(0)
            if state.response.snapshot:return state
            return advance(state,datetime(2026,10,12,tzinfo=UTC),200,record())
        store=Store();owner=Owner(store,None,fetcher=fetch)
        await owner.async_load(confirmed_new=True)
        await asyncio.gather(owner.async_refresh(),owner.async_refresh())
        self.assertIsNotNone(calls[1].response.snapshot)
        self.assertEqual(store.saves,2)
        broken=Owner(store,None,fetcher=lambda *a,**k: fetch(Engine(),None))
        await broken.async_load();old=broken.state;store.fail=True
        with self.assertRaises(OSError):await broken.async_refresh()
        self.assertIs(broken.state,old)
        self.assertTrue(broken.blocked)
