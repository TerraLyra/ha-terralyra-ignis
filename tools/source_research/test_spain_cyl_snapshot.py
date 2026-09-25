import json
import unittest
from spain_cyl_review import inspect_response
from spain_cyl_snapshot import latest_bulletin_indexes


def row(province, day, hour='10:00'):
    return dict(provincia=province, fecha_del_parte=day, hora_del_parte=hour)


class BulletinTests(unittest.TestCase):
    def select(self, rows, total=None):
        return latest_bulletin_indexes(inspect_response(json.dumps(dict(
            total_count=len(rows) if total is None else total, results=rows)).encode()))

    def test_independently_updated_provinces_and_all_ties_retained(self):
        result = self.select([row(['A'],'2026-09-24'), row(['A'],'2026-09-25'),
                              row(['A'],'2026-09-25'), row(['B'],'2026-09-23')])
        self.assertEqual(result['indexes'], [1,2,3])
        self.assertFalse(result['incident_deduplication'])

    def test_partial_sample_never_filters(self):
        result = self.select([row(['A'],'2026-09-24'),row(['A'],'2026-09-25')], 100)
        self.assertFalse(result['applied'])
        self.assertEqual(result['indexes'], [0,1])

    def test_unknown_time_or_scope_is_preserved(self):
        result = self.select([row(['A'],'2026-09-24'), row(['A'],'invalid'), row(None,'2026-09-25')])
        self.assertEqual(result['indexes'], [0,1,2])
        self.assertEqual(result['unresolved_indexes'], [1,2])

    def test_multi_province_scope_is_not_merged_into_one_province(self):
        result = self.select([row(['A','B'],'2026-09-24'), row(['A'],'2026-09-25'),
                              row(['B','A'],'2026-09-23')])
        self.assertEqual(result['indexes'], [0,1])

    def test_empty_response(self):
        self.assertEqual(self.select([])['indexes'], [])
