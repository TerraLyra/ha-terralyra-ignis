import unittest
from datetime import datetime, UTC, timedelta
from tasalert_engine import Engine, advance
from test_tasalert_snapshot import record
from test_tasalert_retention import pair


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.now=datetime(2026,10,12,tzinfo=UTC)
        self.a=record()
        self.b=record(number='B').replace(b'id="one"',b'id="two"')
        self.base=advance(Engine(),self.now,200,pair(self.a,self.b),etag='"a"')

    def test_receipt_clock_survives_failures_and_restart(self):
        import json
        from tasalert_engine_storage import encode, decode
        self.assertEqual(self.base.response.last_success_at,self.now)
        cached=advance(self.base,self.now+timedelta(hours=1),304)
        self.assertEqual(cached.response.last_success_at,self.now+timedelta(hours=1))
        self.assertEqual(cached.ledger,self.base.ledger)
        for status,body in ((503,b''),(200,b'broken'),(200,b'<kml/>')):
            failed=advance(cached,self.now+timedelta(hours=2),status,body)
            restored=decode(encode(failed))
            self.assertEqual(restored.response.last_success_at,cached.response.last_success_at)
        old=json.loads(encode(self.base))
        old['response'].pop('last_success_at')
        self.assertIsNone(decode(json.dumps(old).encode()).response.last_success_at)
        old['response']['last_success_at']='2026-10-12T12:00:00'
        with self.assertRaises(ValueError):decode(json.dumps(old).encode())

    def test_partial_review_and_304_keep_distinct_representations(self):
        changed=record('Patrol','2026-10-12T13:00:00+00:00',number='B').replace(b'id="one"',b'id="two"')
        body=pair(record(number='conflict'),changed)
        updated=advance(self.base,self.now+timedelta(hours=1),200,body,etag='"b"')
        self.assertEqual(updated.review,('one',))
        self.assertEqual(updated.response.snapshot,body)
        self.assertEqual(updated.ledger['one']['record']['fields']['number'],'A')
        self.assertEqual(updated.ledger['two']['record']['fields']['status'],'Patrol')
        cached=advance(updated,self.now+timedelta(hours=2),304)
        self.assertEqual(cached.ledger,updated.ledger)
        self.assertEqual(cached.review,updated.review)
        self.assertEqual(self.base.ledger['two']['record']['fields']['status'],'Going')

    def test_missing_record_not_refreshed_by_304(self):
        missing=advance(self.base,self.now+timedelta(hours=1),200,self.b)
        cached=advance(missing,self.now+timedelta(days=8),304)
        self.assertEqual(cached.ledger['one']['last_seen'],self.now)
        self.assertEqual(cached.ledger['one']['presence'],'not_in_snapshot')
        self.assertEqual(cached.ledger,missing.ledger)

    def test_errors_and_empty_retain_both_layers(self):
        for status,body in [(500,b''),(200,b'broken'),(200,b'<kml xmlns="http://www.opengis.net/kml/2.2"/>')]:
            failed=advance(self.base,self.now+timedelta(hours=1),status,body,etag='"bad"')
            self.assertEqual(failed.ledger,self.base.ledger)
            self.assertEqual(failed.response.snapshot,self.base.response.snapshot)
            self.assertEqual(failed.response.etag,'"a"')
            self.assertEqual(failed.response.failures,1)
