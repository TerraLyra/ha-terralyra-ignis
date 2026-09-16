from datetime import datetime, timezone
import math
import unittest

from nifc_fetch import FetchResult
from nifc_refresh import RefreshState, due, succeeded, failed, retry_after_seconds


class RefreshTests(unittest.TestCase):
    def test_disabled_or_running_never_due(self):
        for enabled, running in ((False,False), (False,True), (True,True)):
            self.assertFalse(due(RefreshState(), now=100, enabled=enabled, in_flight=running))

    def test_success_wait_and_reset(self):
        result = FetchResult((),1,42,'terminal_reported')
        state = succeeded(RefreshState(failures=3), result, now=100)
        self.assertEqual(state.failures, 0)
        self.assertFalse(due(state,now=999,enabled=True,in_flight=False))
        self.assertTrue(due(state,now=1000,enabled=True,in_flight=False))
        self.assertIs(state.last_success, result)

    def test_failure_retains_exact_snapshot_and_receipt(self):
        old = succeeded(RefreshState(),FetchResult((),1,42,'terminal_reported'),now=10)
        for kind in ('transient','rate_limited','invalid_data','access_denied'):
            new = failed(old,now=1000,kind=kind)
            self.assertIs(new.last_success,old.last_success)
            self.assertEqual(new.last_success_at,10)
            self.assertEqual(old.failures,0)

    def test_backoff_caps_without_shortening_server_wait(self):
        state=RefreshState()
        waits=[]
        for _ in range(9):
            state=failed(state,now=0,kind='transient'); waits.append(state.next_attempt_at)
        self.assertEqual(waits[:4],[900,1800,3600,7200])
        self.assertEqual(waits[-1],21600)
        state=failed(state,now=0,kind='rate_limited',server_wait=90000)
        self.assertEqual(state.next_attempt_at,90000)

    def test_manual_review_errors_never_automatically_due(self):
        for kind in ('invalid_data','access_denied'):
            state=failed(RefreshState(),now=0,kind=kind)
            self.assertFalse(due(state,now=10**12,enabled=True,in_flight=False))

    def test_retry_after_seconds_and_dates(self):
        now=datetime(2026,9,16,12,tzinfo=timezone.utc)
        for raw, expected in [('120',120),('0',0),
                              ('Wed, 16 Sep 2026 13:00:00 GMT',3600),
                              ('Wed, 16 Sep 2026 11:00:00 GMT',0)]:
            self.assertEqual(retry_after_seconds(raw,now=now),expected)
        self.assertEqual(retry_after_seconds('9'*100,now=now),math.inf)
        for raw in ('-1','1.2','oops',None,'Wed, 16 Sep 2026 13:00:00'):
            self.assertIsNone(retry_after_seconds(raw,now=now))

    def test_invalid_clock_and_wait_rejected(self):
        for now in (True,-1,float('nan'),float('inf')):
            with self.assertRaises(ValueError): due(RefreshState(),now=now,enabled=True,in_flight=False)
        for wait in (True,-1,float('nan')):
            with self.assertRaises(ValueError): failed(RefreshState(),now=0,kind='transient',server_wait=wait)

    def test_partial_result_cannot_replace_snapshot(self):
        with self.assertRaises(ValueError):
            succeeded(RefreshState(),FetchResult((),1,42,'incomplete'),now=0)

    def test_existing_server_cooldown_is_never_shortened(self):
        state=failed(RefreshState(),now=0,kind='rate_limited',server_wait=90000)
        again=failed(state,now=1,kind='transient')
        self.assertEqual(again.next_attempt_at,90000)
