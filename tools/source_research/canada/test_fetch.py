import json
import unittest
from unittest.mock import patch
from fetch import decode_response

class FetchTests(unittest.TestCase):
    def payload(self, matched=0, returned=0):
        return json.dumps(dict(type='FeatureCollection',features=[],numberMatched=matched,numberReturned=returned)).encode()

    def test_empty_complete(self):
        _, report = decode_response(self.payload())
        self.assertTrue(report['response_count_complete'])
        self.assertEqual(report['national_coverage'],'not_established')

    def test_partial_or_unknown_rejected(self):
        for matched in (1,'unknown',True):
            with self.subTest(matched=matched),self.assertRaises(ValueError):
                decode_response(self.payload(matched))

    def test_size_limit(self):
        with patch('fetch.MAX_BYTES',10),self.assertRaises(ValueError):
            decode_response(self.payload())

    def test_non_json_and_nonfinite_rejected(self):
        for raw in (b'<ExceptionReport/>',b'[]',b'{"n":NaN}'):
            with self.subTest(raw=raw),self.assertRaises(ValueError):
                decode_response(raw)
