import unittest
from datetime import UTC, datetime, timedelta
from email.message import Message
from urllib.error import HTTPError
from unittest.mock import Mock
from retry import RefreshState, retry_after

NOW = datetime(2026,9,21,tzinfo=UTC)

class RetryTests(unittest.TestCase):
    def error(self, code, retry=None):
        headers=Message()
        if retry: headers['Retry-After']=retry
        return HTTPError('https://example.invalid',code,'synthetic',headers,None)

    def test_success_failure_recovery_preserves_previous_response(self):
        state=RefreshState(); fetch=Mock(return_value=('first',{}))
        self.assertTrue(state.refresh(fetch,NOW))
        self.assertFalse(state.refresh(fetch,NOW+timedelta(minutes=1)))
        self.assertEqual(fetch.call_count,1)
        fetch.side_effect=TimeoutError()
        self.assertFalse(state.refresh(fetch,NOW+timedelta(hours=1)))
        self.assertEqual(state.last_success,('first',{}))
        self.assertEqual(state.last_success_at,NOW)
        fetch.side_effect=None; fetch.return_value=('second',{})
        self.assertTrue(state.refresh(fetch,state.next_attempt))
        self.assertEqual(state.failures,0)

    def test_server_delay_not_shortened(self):
        state=RefreshState(); fetch=Mock(side_effect=self.error(429,'7200'))
        state.refresh(fetch,NOW)
        self.assertEqual(state.next_attempt,NOW+timedelta(hours=2))
        self.assertEqual(state.status,'rate_limited')
        state.refresh(fetch,NOW+timedelta(hours=1))
        self.assertEqual(fetch.call_count,1)

    def test_auth_and_missing_endpoint_stop_automatic_retries(self):
        for code in (401,403,404):
            with self.subTest(code=code):
                state=RefreshState(); fetch=Mock(side_effect=self.error(code))
                state.refresh(fetch,NOW);state.refresh(fetch,NOW+timedelta(days=1))
                self.assertTrue(state.review_required)
                self.assertEqual(fetch.call_count,1)

    def test_rejected_payload_does_not_replace_good_data(self):
        state=RefreshState(last_success='retained')
        state.refresh(Mock(side_effect=ValueError('partial')),NOW)
        self.assertEqual(state.last_success,'retained')
        self.assertEqual(state.status,'invalid_response')

    def test_retry_after_dates_and_invalid_values(self):
        self.assertEqual(retry_after('Mon, 21 Sep 2026 02:00:00 GMT',NOW),NOW+timedelta(hours=2))
        for value in ('garbage','-10','Sun, 20 Sep 2026 02:00:00 GMT'):
            self.assertIsNone(retry_after(value,NOW))

    def test_backoff_increases_and_is_bounded(self):
        state=RefreshState();now=NOW
        for minutes in (5,10,20,40,80,160,320,320):
            state.refresh(Mock(side_effect=TimeoutError()),now)
            self.assertEqual(state.next_attempt-now,timedelta(minutes=minutes))
            now=state.next_attempt
