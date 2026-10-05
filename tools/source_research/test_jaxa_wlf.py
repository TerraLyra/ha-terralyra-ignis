"""Synthetic preflight tests; no assertion about real upstream column spelling."""
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from jaxa_wlf import CUTOFF, eligible_observation_time, inspect_structure


class WlfTests(unittest.TestCase):
    def test_date_boundary(self):
        self.assertFalse(eligible_observation_time(CUTOFF - timedelta(microseconds=1)))
        self.assertTrue(eligible_observation_time(CUTOFF))
        self.assertTrue(eligible_observation_time(CUTOFF + timedelta(days=1)))

    def test_offset_is_an_instant_not_wall_time(self):
        east = timezone(timedelta(hours=9))
        self.assertTrue(eligible_observation_time(datetime(2026, 2, 1, 9, tzinfo=east)))
        self.assertFalse(eligible_observation_time(datetime(2026, 2, 1, 8, 59, tzinfo=east)))
        west = timezone(timedelta(hours=-5))
        self.assertTrue(eligible_observation_time(datetime(2026, 1, 31, 19, tzinfo=west)))

    def test_missing_and_naive_times_rejected(self):
        for value in (None, datetime(2026, 10, 1), '2026-10-01'):
            self.assertFalse(eligible_observation_time(value))

    def test_headers_preserved_without_claiming_semantics(self):
        result = inspect_structure(b'# synthetic time\r\n# synthetic columns\r\n1,2,3\r\n4,5,6\r\n')
        self.assertEqual(result.headers, ('# synthetic time', '# synthetic columns'))
        self.assertEqual((result.row_count, result.column_count), (2, 3))
        self.assertFalse(result.semantics_verified)
        self.assertEqual(len(result.sha256), 64)

    def test_header_only_is_not_verified_no_fire(self):
        result = inspect_structure(b'# one\n# two\n')
        self.assertEqual(result.row_count, 0)
        self.assertIsNone(result.column_count)
        self.assertFalse(result.semantics_verified)

    def test_bad_samples(self):
        for sample in (b'', b'<html>error</html>', b'# one\n1,2',
                       b'# one\n# two\n1,2\n3,4,5', b'# one\n# two\n# extra',
                       b'# one\n# two\nabc', b'# one\n# two\n1,\x00',
                       b'# one\n# two\n"unfinished,2'):
            with self.subTest(sample=sample), self.assertRaises(ValueError):
                inspect_structure(sample)

    def test_limits(self):
        sample = b'# one\n# two\n1,2\n3,4'
        for limit, value in [('MAX_BYTES', 5), ('MAX_LINE', 3), ('MAX_ROWS', 1)]:
            with self.subTest(limit=limit), patch('jaxa_wlf.' + limit, value):
                with self.assertRaises(ValueError):
                    inspect_structure(sample)

    def test_encoding(self):
        self.assertEqual(inspect_structure(b'\xef\xbb\xbf# one\n# two\n1,2').row_count, 1)
        with self.assertRaises(UnicodeDecodeError):
            inspect_structure(b'# one\n# two\n\xff,2')
