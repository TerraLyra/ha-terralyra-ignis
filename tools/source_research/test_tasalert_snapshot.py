"""Synthetic lifecycle cases; no live state or upstream requests."""
import unittest
from tasalert_snapshot import compare_snapshots
from test_tasalert_kml import sample


def record(status='Going', changed='2026-10-12T12:00:00+00:00', number='A'):
    return sample(extra=''.join(f'<Data name="{k}"><value>{v}</value></Data>' for k,v in
        [('status', status), ('number', number), ('created','2026-10-11T12:00:00+00:00'), ('changed',changed)]))


class SnapshotTests(unittest.TestCase):
    def state(self, before, after):
        return compare_snapshots(before,after)['changes'][0]

    def test_repeat_is_idempotent(self):
        self.assertEqual(self.state(record(),record())['state'],'unchanged')

    def test_update_keeps_source_status_not_extinction(self):
        result=self.state(record(),record('Patrol','2026-10-12T13:00:00+00:00'))
        self.assertEqual(result['state'],'updated')
        self.assertEqual(result['current']['fields']['status'],'Patrol')
        self.assertEqual(result['previous']['fields']['status'],'Going')

    def test_missing_and_returning_do_not_create_lifecycle_claim(self):
        empty=b'<kml xmlns="http://www.opengis.net/kml/2.2"/>'
        result=compare_snapshots(record(),empty)
        self.assertTrue(result['empty_current_snapshot'])
        self.assertFalse(result['deletes_records'])
        self.assertFalse(result['infers_extinction'])
        self.assertEqual(result['changes'][0]['state'],'not_in_snapshot')
        self.assertIsNotNone(result['changes'][0]['previous'])
        self.assertEqual(self.state(empty,record())['state'],'first_seen')

    def test_regression_and_identity_change_require_review(self):
        for after in (record(changed='2026-10-12T11:00:00+00:00'),record(number='B'),record(status='Patrol')):
            self.assertEqual(self.state(record(),after)['state'],'review_required')

    def test_equivalent_offsets_do_not_advance_clock(self):
        after=record(status='Patrol',changed='2026-10-12T23:00:00+11:00')
        self.assertIn('content_changed_without_advancing_clock',self.state(record(),after)['reasons'])

    def test_invalid_snapshot_produces_no_plan(self):
        with self.assertRaises(Exception):compare_snapshots(record(),b'<broken')
