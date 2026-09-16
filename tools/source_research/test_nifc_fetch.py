import json
import unittest
from urllib.parse import parse_qs, urlsplit
from unittest.mock import patch

from nifc_fetch import fetch_incidents, read_url, _NoRedirect
from test_nifc_records import sample


def encoded(oid=1, more=False, empty=False):
    page = sample()
    page['exceededTransferLimit'] = more
    if empty:
        page['features'] = []
    else:
        attrs = page['features'][0]['attributes']
        attrs['OBJECTID'] = oid
        attrs['IrwinID'] = f'12345678-1234-1234-1234-{oid:012d}'
    return json.dumps(page).encode()


class FetchTests(unittest.TestCase):
    def run_pages(self, payloads, **kwargs):
        calls = []
        def reader(url, limit, timeout):
            calls.append((parse_qs(urlsplit(url).query), limit, timeout))
            return payloads[len(calls)-1]
        return fetch_incidents(reader=reader, **kwargs), calls

    def test_short_and_empty_pages_advance_requested_offset(self):
        result, calls = self.run_pages([encoded(more=True), encoded(empty=True, more=True), encoded(3)], page_size=5)
        self.assertEqual([c[0]['resultOffset'] for c in calls], [['0'], ['5'], ['10']])
        self.assertEqual(len(result.records), 2)
        self.assertEqual(result.snapshot_consistency, 'not_established')
        self.assertTrue(all(c[0]['where'] == ['1=1'] and c[0]['outSR'] == ['4326'] for c in calls))

    def test_missing_continuation_aborts(self):
        page = sample(); page.pop('exceededTransferLimit')
        with self.assertRaises(ValueError): self.run_pages([json.dumps(page).encode()])

    def test_page_and_record_budgets(self):
        for limits in ({'max_pages': 1}, {'max_records': 1}):
            with self.assertRaises(ValueError): self.run_pages([encoded(more=True)], **limits)

    def test_byte_budget_is_passed_to_reader(self):
        first, second = encoded(more=True), encoded(2)
        with self.assertRaises(ValueError): self.run_pages([first], max_page_bytes=len(first)-1)
        result, calls = self.run_pages([first, second], max_total_bytes=len(first)+len(second))
        self.assertEqual(calls[1][1], len(second))
        self.assertEqual(result.byte_count, len(first)+len(second))
        with self.assertRaises(ValueError): self.run_pages([first, second], max_total_bytes=len(first)+len(second)-1)

    def test_cross_page_object_and_incident_conflicts(self):
        for second in (encoded(1), encoded(2).replace(b'000000000002', b'000000000001')):
            with self.assertRaises(ValueError): self.run_pages([encoded(more=True), second])

    def test_bad_json_and_service_errors(self):
        for raw in (b'{', b'\xff', b'{"a":1,"a":2}', b'{"a":NaN}', b'{"error":{"code":500}}'):
            with self.subTest(raw=raw), self.assertRaises(ValueError): self.run_pages([raw])

    def test_invalid_limits_never_call_reader(self):
        for kwargs in ({'page_size':2001}, {'timeout':True}, {'max_pages':0}, {'max_total_bytes':-1}):
            with self.assertRaises(ValueError): self.run_pages([], **kwargs)

    def test_network_error_propagates_without_partial_success(self):
        def reader(*args): raise TimeoutError('synthetic timeout')
        with self.assertRaises(TimeoutError): fetch_incidents(reader=reader)

    def test_http_read_is_bounded_and_response_closed(self):
        with patch('nifc_fetch.build_opener') as opener:
            response = opener.return_value.open.return_value.__enter__.return_value
            response.status = 200; response.headers = {}; response.read.return_value = b'12345'
            with self.assertRaises(ValueError): read_url('https://example.invalid', 4, 2)
            response.read.assert_called_once_with(5)
            opener.return_value.open.return_value.__exit__.assert_called_once()

    def test_redirect_is_not_followed(self):
        self.assertIsNone(_NoRedirect().redirect_request(None, None, 302, None, None, 'https://example.invalid'))
