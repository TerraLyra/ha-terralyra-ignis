import unittest
from datetime import datetime
from act_feed import ActItem
from act_times import inspect_times


def item(description='', publication=None):
    fields = [('description', description)]
    if publication is not None:
        fields.append(('pubDate', publication))
    return ActItem(tuple(fields))


class TimeTests(unittest.TestCase):
    def test_three_independent_source_times(self):
        result = inspect_times(item('Updated: 16 Sep 2026 22:54:31.2\rTime of Call: 16 Sep 2026 18:10:24',
                                    '2026-09-16 23:27 AEST'))
        self.assertEqual(result.updated.wall_time, datetime(2026,9,16,22,54,31,200000))
        self.assertEqual(result.call.wall_time.hour, 18)
        self.assertEqual(result.publication.wall_time.hour, 23)
        self.assertEqual(result.publication.zone_label, 'AEST')
        for value in (result.updated, result.call, result.publication):
            self.assertEqual(value.status, 'timezone_unverified')
            self.assertIsNone(value.wall_time.tzinfo)

    def test_missing_has_no_publication_fallback(self):
        result = inspect_times(item(publication='2026-09-16 23:27 AEST'))
        self.assertEqual(result.updated.status, 'missing')
        self.assertIsNone(result.updated.wall_time)
        self.assertEqual(result.call.status, 'missing')

    def test_duplicate_labels_never_choose_one(self):
        for separator in ('\r', '\n', '\r\n'):
            result = inspect_times(item(separator.join(['Updated: 16 Sep 2026 22:54:31']*2)))
            self.assertEqual(result.updated.status, 'duplicate')
            self.assertIsNone(result.updated.wall_time)

    def test_invalid_dates_and_unknown_formats(self):
        for raw in ('31 Feb 2026 01:02:03', '16 Xxx 2026 01:02:03',
                    '16 Sep 2026 24:00:00', '16 Sep 2026 22:54:31.1234567', '',
                    '2026-09-16T22:54:31Z'):
            with self.subTest(raw=raw):
                result = inspect_times(item('Updated: '+raw))
                self.assertEqual(result.updated.status, 'invalid')
                self.assertEqual(result.updated.raw_values, (raw,))

    def test_dst_wall_times_not_silently_resolved(self):
        for raw in ('5 Apr 2026 02:30:00', '4 Oct 2026 02:30:00'):
            self.assertEqual(inspect_times(item('Updated: '+raw)).updated.status, 'timezone_unverified')
        for zone in ('AEST','AEDT'):
            self.assertEqual(inspect_times(item(publication='2026-01-01 12:00 '+zone)).publication.status,
                             'timezone_unverified')

    def test_no_embedded_text_matching(self):
        self.assertEqual(inspect_times(item('Note: Updated: 16 Sep 2026 22:54:31')).updated.status, 'missing')

    def test_bad_publication_and_duplicate_fields(self):
        self.assertEqual(inspect_times(item(publication='2026-09-16 23:27 XYZ')).publication.status, 'invalid')
        with self.assertRaises(ValueError):
            inspect_times(ActItem((('pubDate','a'),('pubDate','b'))))
