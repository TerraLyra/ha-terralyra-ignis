import io
import unittest
from datetime import datetime, UTC, timedelta
from urllib.error import HTTPError, URLError
from tasalert_fetch import fetch_once, URL, TIMEOUT, NoRedirects
from tasalert_engine import Engine, advance
from tasalert_kml import MAX_BYTES
from test_tasalert_snapshot import record


class Response(io.BytesIO):
    def __init__(self,body=b'',code=200,headers=None):
        super().__init__(body);self.code=code;self.headers=headers or {}


class Transport:
    def __init__(self,response):self.response=response;self.calls=[]
    def open(self,request,timeout):
        self.calls.append((request,timeout))
        if isinstance(self.response,Exception):raise self.response
        return self.response


class FetchTests(unittest.TestCase):
    def setUp(self):
        self.now=datetime(2026,10,12,tzinfo=UTC)
        self.base=advance(Engine(),self.now,200,record(),etag='"old"')
        self.later=self.now+timedelta(hours=1)

    def run_fetch(self,response,engine=None):
        transport=Transport(response)
        result=fetch_once(engine or self.base,clock=lambda:self.later,opener=transport)
        self.assertEqual(len(transport.calls),1)
        return result,transport

    def test_conditional_request_and_304(self):
        result,t=self.run_fetch(HTTPError(URL,304,'Not Modified',{},io.BytesIO()))
        self.assertEqual(result.ledger,self.base.ledger)
        self.assertEqual(result.response.status,'not_modified')
        request,timeout=t.calls[0]
        self.assertEqual(request.full_url,URL)
        self.assertEqual(request.get_header('If-none-match'),'"old"')
        self.assertEqual(timeout,TIMEOUT)

    def test_not_due_does_no_io(self):
        t=Transport(None)
        self.assertIs(fetch_once(self.base,clock=lambda:self.now,opener=t),self.base)
        self.assertEqual(t.calls,[])

    def test_valid_payload_and_closed_response(self):
        response=Response(record(),headers={'ETag':'"new"'})
        result,_=self.run_fetch(response)
        self.assertEqual(result.response.etag,'"new"')
        self.assertTrue(response.closed)

    def test_failures_preserve_data(self):
        for response in (Response(b'x'*(MAX_BYTES+1)),Response(record(),headers={'Content-Length':'99999999'}),Response(record(),headers={'Content-Encoding':'gzip'}),Response(b'x',headers={'Content-Length':'2'}),Response(b'<broken'),URLError('offline')):
            result,_=self.run_fetch(response)
            self.assertEqual(result.response.snapshot,self.base.response.snapshot)
            self.assertEqual(result.ledger,self.base.ledger)
            self.assertEqual(result.response.failures,1)

    def test_retry_after_and_redirect_refusal(self):
        result,_=self.run_fetch(HTTPError(URL,429,'Limited',{'Retry-After':'7200'},io.BytesIO()))
        self.assertEqual(result.response.next_attempt,self.later+timedelta(hours=2))
        self.assertIsNone(NoRedirects().redirect_request(None,None,302,'',{},'https://other.example'))
        result,_=self.run_fetch(Response(code=302))
        self.assertEqual(result.response.status,'retrieval_failed')
