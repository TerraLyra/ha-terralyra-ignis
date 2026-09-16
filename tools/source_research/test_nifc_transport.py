"""Transport contract tests with synthetic streamed HTTP responses."""
import asyncio
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from nifc_async import _read
from nifc_refresh import SourceHTTPError


class Response:
    def __init__(self, chunks=(), status=200, headers=None):
        self.status, self.headers = status, headers or {}
        self.chunks, self.closed, self.read_count = chunks, False, 0
        self.content = self

    async def __aenter__(self): return self
    async def __aexit__(self, *args): self.closed = True
    async def iter_chunked(self, size):
        for chunk in self.chunks:
            self.read_count += 1
            yield chunk


class TransportTests(unittest.IsolatedAsyncioTestCase):
    async def read(self, response, cap=4):
        def get(url, **kwargs):
            self.assertFalse(kwargs['allow_redirects'])
            self.assertEqual(kwargs['headers']['Accept-Encoding'], 'identity')
            self.assertEqual(kwargs['timeout'].total, 2)
            return response
        with patch.dict(sys.modules, {'aiohttp':SimpleNamespace(ClientTimeout=lambda **kw: SimpleNamespace(**kw))}):
            return await _read(SimpleNamespace(get=get), 'https://example.invalid', cap, 2)

    async def test_stream_assembled_and_closed(self):
        response = Response([b'ab', b'cd'])
        self.assertEqual(await self.read(response), b'abcd')
        self.assertTrue(response.closed)

    async def test_oversize_stops_before_remaining_chunks(self):
        response = Response([b'abc', b'de', b'not consumed'])
        with self.assertRaises(ValueError): await self.read(response)
        self.assertEqual(response.read_count, 2)
        self.assertTrue(response.closed)

    async def test_redirect_rate_limit_server_error_and_compression_rejected(self):
        for status, headers in [(302, {}), (429, {}), (503, {}), (200, {'Content-Encoding':'gzip'})]:
            response = Response([b'ignored'], status, headers)
            with self.subTest(status=status, headers=headers), self.assertRaises(ValueError):
                await self.read(response)
            self.assertEqual(response.read_count, 0)
            self.assertTrue(response.closed)

    async def test_cancellation_during_body_closes_response(self):
        started = asyncio.Event()
        class SlowResponse(Response):
            async def iter_chunked(self, size):
                started.set()
                await asyncio.Future()
                yield b''
        response = SlowResponse()
        task = asyncio.create_task(self.read(response))
        await started.wait()
        task.cancel()
        with self.assertRaises(asyncio.CancelledError): await task
        self.assertTrue(response.closed)

    async def test_rate_limit_metadata_survives_without_body(self):
        response = Response([b'not retained'],429,{'Retry-After':'3600'})
        with self.assertRaises(SourceHTTPError) as caught:
            await self.read(response)
        self.assertEqual(caught.exception.status,429)
        self.assertEqual(caught.exception.retry_after,'3600')
        self.assertEqual(response.read_count,0)
        self.assertTrue(response.closed)
