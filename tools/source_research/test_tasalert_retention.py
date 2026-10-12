import unittest
from datetime import datetime, UTC, timedelta
from tasalert_retention import reconcile
from test_tasalert_snapshot import record


def pair(first,second):
    a=first.decode();b=second.decode()
    mark=b[b.index('<Placemark'):b.index('</Placemark>')+12]
    return a.replace('</Document>',mark+'</Document>').encode()


class RetentionTests(unittest.TestCase):
    def setUp(self):
        self.now=datetime(2026,10,12,tzinfo=UTC)
        self.one=record()
        self.two=record(number='B').replace(b'id="one"',b'id="two"')
        self.ledger=reconcile({},pair(self.one,self.two),self.now)['records']

    def test_partial_update_is_not_blocked_by_conflict(self):
        conflict=record(number='changed')
        updated=record('Patrol','2026-10-12T13:00:00+00:00',number='B').replace(b'id="one"',b'id="two"')
        result=reconcile(self.ledger,pair(conflict,updated),self.now+timedelta(hours=1))
        self.assertEqual(result['review'],['one'])
        self.assertEqual(result['records']['one']['record']['fields']['number'],'A')
        self.assertEqual(result['records']['two']['record']['fields']['status'],'Patrol')
        self.assertEqual(self.ledger['two']['record']['fields']['status'],'Going')

    def test_missing_retained_then_local_expiry(self):
        first=reconcile(self.ledger,self.two,self.now+timedelta(days=1))
        self.assertEqual(first['records']['one']['presence'],'not_in_snapshot')
        final=reconcile(first['records'],self.two,self.now+timedelta(days=7))
        self.assertEqual(final['expired'],['one'])
        self.assertNotIn('one',final['records'])

    def test_return_refreshes_presence_without_new_fire_claim(self):
        missing=reconcile(self.ledger,self.two,self.now+timedelta(days=1))['records']
        result=reconcile(missing,pair(self.one,self.two),self.now+timedelta(days=2))
        self.assertEqual(result['records']['one']['presence'],'in_snapshot')
        self.assertEqual(result['expired'],[])

    def test_invalid_and_empty_do_not_erase(self):
        with self.assertRaises(Exception):reconcile(self.ledger,b'broken',self.now)
        result=reconcile(self.ledger,b'<kml xmlns="http://www.opengis.net/kml/2.2"/>',self.now+timedelta(days=90))
        self.assertEqual(result['records'],self.ledger)
        self.assertEqual(result['expired'],[])

    def test_receipt_clock_regression_rejected(self):
        with self.assertRaises(ValueError):reconcile(self.ledger,self.two,self.now-timedelta(seconds=1))
