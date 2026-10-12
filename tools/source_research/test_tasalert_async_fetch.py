import asyncio
import unittest
from datetime import datetime, UTC, timedelta
from tasalert_async_fetch import fetch_once
from tasalert_engine import Engine, advance
from tasalert_kml import MAX_BYTES
from test_tasalert_snapshot import record


class Response:
    def __init__(self,chunks=(),status=200,headers=None,wait=False):
        self.chunks=chunks;self.status=status;self.headers=headers or {};self.wait=wait;self.content=self;self.closed=False
    async def __aenter__(self):return self
    async def __aexit__(self,*args):self.closed=True
    async def iter_chunked(self,size):
        if self.wait:await asyncio.Event().wait()
        for chunk in self.chunks:yield chunk


class Session:
    def __init__(self,response):self.response=response;self.calls=[]
    def get(self,*args,**kwargs):self.calls.append((args,kwargs));return self.response


class AsyncTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.now=datetime(2026,10,12,tzinfo=UTC)
        self.base=advance(Engine(),self.now-timedelta(hours=1),200,record(),etag='"old"')

    async def test_success_stream_and_request_policy(self):
        raw=record();response=Response([raw[:20],raw[20:]],headers={'ETag':'"new"'})
        session=Session(response)
        result=await fetch_once(self.base,session,clock=lambda:self.now)
        self.assertEqual(result.response.etag,'"new"')
        self.assertTrue(response.closed)
        self.assertFalse(session.calls[0][1]['allow_redirects'])
        self.assertEqual(session.calls[0][1]['headers']['If-None-Match'],'"old"')

    async def test_total_timeout_preserves_state(self):
        response=Response(wait=True)
        result=await fetch_once(self.base,Session(response),clock=lambda:self.now,total_timeout=.01)
        self.assertEqual(result.response.snapshot,self.base.response.snapshot)
        self.assertEqual(result.response.failures,1)
        self.assertTrue(response.closed)

    async def test_cancel_propagates_without_mutating_input(self):
        response=Response(wait=True)
        task=asyncio.create_task(fetch_once(self.base,Session(response),clock=lambda:self.now))
        await asyncio.sleep(0)
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):await task
        self.assertTrue(response.closed)
        self.assertEqual(self.base.response.failures,0)

    async def test_oversize_and_truncation_retain_data(self):
        for response in (Response([b'x'*MAX_BYTES,b'x']),Response([b'x'],headers={'Content-Length':'2'})):
            result=await fetch_once(self.base,Session(response),clock=lambda:self.now)
            self.assertEqual(result.ledger,self.base.ledger)
            self.assertEqual(result.response.failures,1)
            self.assertTrue(response.closed)

    async def test_due_gate_and_304(self):
        session=Session(Response(status=304))
        result=await fetch_once(self.base,session,clock=lambda:self.now)
        self.assertEqual(result.ledger,self.base.ledger)
        fresh=Session(None)
        self.assertIs(await fetch_once(result,fresh,clock=lambda:self.now),result)
        self.assertEqual(fresh.calls,[])

    async def test_explicit_transport_error_gets_backoff(self):
        class PayloadError(Exception):pass
        class Broken(Response):
            async def iter_chunked(self,size):
                raise PayloadError('incomplete response')
                yield b''
        response=Broken()
        result=await fetch_once(self.base,Session(response),clock=lambda:self.now,transport_errors=(PayloadError,OSError))
        self.assertEqual(result.response.failures,1)
        self.assertEqual(result.ledger,self.base.ledger)
        self.assertTrue(response.closed)
