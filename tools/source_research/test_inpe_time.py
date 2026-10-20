from datetime import date, datetime, timezone
from unittest import TestCase
from inpe_time import parse_source_time


class SourceTimeTests(TestCase):
    def test_date_does_not_become_midnight_observation(self):
        value = parse_source_time('2026-10-19')
        self.assertIs(type(value), date)
        self.assertEqual(value, date(2026, 10, 19))

    def test_naive_and_explicit_utc_are_same_in_every_local_timezone(self):
        expected = datetime(2026, 10, 19, 23, 45, 6, tzinfo=timezone.utc)
        for value in ('2026-10-19 23:45:06', '2026-10-19T23:45:06Z',
                      '2026-10-19T23:45:06+00:00'):
            self.assertEqual(parse_source_time(value), expected)

    def test_missing_is_unknown_and_malformed_is_not_silently_missing(self):
        self.assertIsNone(parse_source_time(None))
        for value in ('', '2026-02-30', '2026-10-19T25:00:00',
                      '2026-10-19T12:00:00-03:00', '19/10/2026', 0, True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_source_time(value)
