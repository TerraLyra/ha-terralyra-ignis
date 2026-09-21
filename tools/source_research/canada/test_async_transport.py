import asyncio
import unittest
import aiohttp
from aiohttp import web
from aiohttp.test_utils import TestServer
from async_transport import read_json

class TransportTests(unittest.IsolatedAsyncioTestCase):
    async def setup_server(self, handler):
        app=web.Application();app.router.add_get('/',handler)
        server=TestServer(app);await server.start_server()
        self.addAsyncCleanup(server.close)
        session=aiohttp.ClientSession();self.addAsyncCleanup(session.close)
        return session,str(server.make_url('/'))

    async def test_slow_headers_hit_total_deadline(self):
        async def handler(request):
            await asyncio.sleep(.3)
            return web.json_response({})
        session,url=await self.setup_server(handler)
        with self.assertRaises(TimeoutError):
            await read_json(session,url,seconds=.05)

    async def test_trickle_cannot_extend_total_deadline(self):
        async def handler(request):
            response=web.StreamResponse(headers={'Content-Type':'application/json'})
            await response.prepare(request)
            try:
                for _ in range(20):
                    await response.write(b' ');await asyncio.sleep(.02)
            except ConnectionResetError:
                pass
            return response
        session,url=await self.setup_server(handler)
        with self.assertRaises(TimeoutError):
            await read_json(session,url,seconds=.08)

    async def test_stream_size_cap(self):
        async def handler(request):
            response=web.StreamResponse(headers={'Content-Type':'application/json'})
            await response.prepare(request);await response.write(b' '*100)
            return response
        session,url=await self.setup_server(handler)
        with self.assertRaises(ValueError):await read_json(session,url,max_bytes=10)

    async def test_redirect_is_not_followed(self):
        async def handler(request):
            return web.Response(status=302,headers={'Location':'https://example.invalid/'})
        session,url=await self.setup_server(handler)
        with self.assertRaises(ValueError):await read_json(session,url)

    async def test_success(self):
        async def handler(request):return web.json_response({'ok':True})
        session,url=await self.setup_server(handler)
        self.assertEqual(await read_json(session,url),b'{"ok": true}')

    async def test_truncated_body_is_not_accepted(self):
        async def handler(request):
            response=web.StreamResponse(headers={'Content-Type':'application/json','Content-Length':'100'})
            await response.prepare(request);await response.write(b'{}')
            request.transport.close()
            return response
        session,url=await self.setup_server(handler)
        with self.assertRaises(aiohttp.ClientPayloadError):
            await read_json(session,url)
