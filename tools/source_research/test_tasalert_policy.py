import unittest
from datetime import datetime, UTC, timedelta
from tasalert_policy import State, apply_response, request_headers
from test_tasalert_snapshot import record


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.now=datetime(2026,10,12,12,tzinfo=UTC)
        self.good=apply_response(State(),self.now,200,record(),etag='"a"')
        self.later=self.now+timedelta(hours=1)

    def test_conditional_request_and_304(self):
        self.assertEqual(request_headers(self.good),{'If-None-Match':'"a"'})
        result=apply_response(self.good,self.later,304)
        self.assertEqual(result.snapshot,self.good.snapshot)
        self.assertEqual(result.status,'not_modified')
        self.assertEqual(apply_response(State(),self.now,304).status,'unexpected_304')

    def test_bad_response_retains_bytes_and_validator(self):
        for status,body in [(500,b''),(200,b'<broken'),(200,b'<kml xmlns="http://www.opengis.net/kml/2.2"/>'),(200,record(number='other'))]:
            result=apply_response(self.good,self.later,status,body,etag='"bad"')
            self.assertEqual(result.snapshot,self.good.snapshot)
            self.assertEqual(result.etag,'"a"')
            self.assertEqual(result.failures,1)

    def test_backoff_and_retry_after(self):
        first=apply_response(self.good,self.later,429,retry_after='7200')
        self.assertEqual(first.next_attempt,self.later+timedelta(hours=2))
        second=apply_response(first,first.next_attempt,503)
        self.assertEqual(second.next_attempt,first.next_attempt+timedelta(hours=1))
        dated=apply_response(self.good,self.later,503,retry_after='Mon, 12 Oct 2026 18:00:00 GMT')
        self.assertEqual(dated.next_attempt.hour,18)

    def test_due_gate_and_timezone(self):
        with self.assertRaises(ValueError):apply_response(self.good,self.now,200,record())
        with self.assertRaises(ValueError):apply_response(State(),self.now.replace(tzinfo=None),500)

    def test_success_resets_backoff_and_validator_injection_rejected(self):
        result=apply_response(State(failures=4),self.now,200,record(),etag='bad\r\nHeader: value')
        self.assertEqual(result.failures,0)
        self.assertEqual(request_headers(result),{})
