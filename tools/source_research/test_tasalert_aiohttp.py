"""Loopback-only actual aiohttp integration; requires optional aiohttp dependency."""
import asyncio
from datetime import datetime, UTC
import unittest
from unittest.mock import patch
try:
    import aiohttp
    from aiohttp import web
except ImportError:
    aiohttp = None
from tasalert_async_fetch import fetch_once
from tasalert_engine import Engine
from test_tasalert_snapshot import record


@unittest.skipIf(aiohttp is None, 'Optional aiohttp transport dependency unavailable')
class AiohttpTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.now=datetime(2026,10,12,tzinfo=UTC)
        self.mode='ok';self.requests=[];self.release=asyncio.Event()
        async def handler(request):
            self.requests.append(request)
            if self.mode=='slow':
                await self.release.wait()
            if self.mode=='redirect':raise web.HTTPFound('/destination')
            if self.mode=='limited':return web.Response(status=429,headers={'Retry-After':'7200'})
            if self.mode=='conditional' and request.headers.get('If-None-Match')=='"a"':
                return web.Response(status=304)
            return web.Response(body=record(),headers={'ETag':'"a"'})
        app=web.Application();app.router.add_get('/feed',handler)
        self.runner=web.AppRunner(app);await self.runner.setup()
        site=web.TCPSite(self.runner,'127.0.0.1',0);await site.start()
        port=self.runner.addresses[0][1]
        self.url_patch=patch('tasalert_async_fetch.URL',f'http://127.0.0.1:{port}/feed')
        self.url_patch.start()
        self.session=aiohttp.ClientSession()

    async def asyncTearDown(self):
        self.release.set()
        await self.session.close();await self.runner.cleanup();self.url_patch.stop()

    async def fetch(self,state=None,**kwargs):
        return await fetch_once(state or Engine(),self.session,clock=lambda:self.now,
                                transport_errors=(aiohttp.ClientError,OSError),**kwargs)

    async def test_real_session_conditional_response(self):
        from datetime import timedelta
        first=await self.fetch()
        self.assertEqual(first.response.status,'accepted')
        self.now+=timedelta(hours=1);self.mode='conditional'
        second=await self.fetch(first)
        self.assertEqual(second.response.status,'not_modified')
        self.assertEqual(second.ledger,first.ledger)
        self.assertEqual(len(self.requests),2)

    async def test_redirect_is_not_followed(self):
        self.mode='redirect'
        result=await self.fetch()
        self.assertEqual(result.response.status,'retrieval_failed')
        self.assertEqual(len(self.requests),1)

    async def test_real_socket_total_timeout(self):
        self.mode='slow'
        result=await self.fetch(total_timeout=.05)
        self.assertEqual(result.response.failures,1)
        self.assertIsNone(result.response.snapshot)

    async def test_rate_limit_header(self):
        self.mode='limited'
        result=await self.fetch()
        self.assertEqual((result.response.next_attempt-self.now).total_seconds(),7200)
