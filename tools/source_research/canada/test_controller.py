import asyncio
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock
import aiohttp
from controller import Controller
from storage import load

NOW=datetime(2026,9,21,tzinfo=UTC)
EMPTY=({'type':'FeatureCollection','features':[],'numberMatched':0,'numberReturned':0},{})

class ControllerTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'state.json'
        self.time=NOW

    def owner(self, fetch):
        return Controller(self.path,None,clock=lambda:self.time,fetcher=fetch)

    async def test_concurrent_calls_fetch_once_and_restart_honors_pause(self):
        fetch=AsyncMock(return_value=EMPTY);owner=self.owner(fetch)
        await asyncio.gather(owner.refresh(),owner.refresh())
        await self.owner(fetch).refresh()
        self.assertEqual(fetch.await_count,1)

    async def test_receipt_clock_and_failure_keep_cache(self):
        async def fetch(session):
            self.time+=timedelta(seconds=20)
            return EMPTY
        state=await self.owner(fetch).refresh()
        self.assertEqual(state.last_success_at,NOW+timedelta(seconds=20))
        self.time+=timedelta(hours=2)
        state=await self.owner(AsyncMock(side_effect=TimeoutError())).refresh()
        self.assertEqual(state.status,'unavailable')
        self.assertEqual(state.last_success[0],EMPTY[0])
        self.assertEqual(state.last_success_at,NOW+timedelta(seconds=20))

    async def test_cancellation_retains_reservation(self):
        entered=asyncio.Event()
        async def fetch(session):
            entered.set();await asyncio.Event().wait()
        task=asyncio.create_task(self.owner(fetch).refresh())
        await entered.wait();task.cancel()
        with self.assertRaises(asyncio.CancelledError):await task
        self.assertEqual(load(self.path).next_attempt,NOW+timedelta(hours=1))
        fetch2=AsyncMock();await self.owner(fetch2).refresh();fetch2.assert_not_awaited()

    async def test_rate_limit_survives_restart(self):
        error=aiohttp.ClientResponseError(None,(),status=429,headers={'Retry-After':'7200'})
        state=await self.owner(AsyncMock(side_effect=error)).refresh()
        self.assertEqual(state.status,'rate_limited')
        self.assertEqual(load(self.path).next_attempt,NOW+timedelta(hours=2))

    async def test_invalid_response_retains_cache(self):
        await self.owner(AsyncMock(return_value=EMPTY)).refresh()
        self.time+=timedelta(hours=2)
        state=await self.owner(AsyncMock(side_effect=ValueError('partial'))).refresh()
        self.assertEqual(state.status,'invalid_response')
        self.assertEqual(state.last_success[0],EMPTY[0])
