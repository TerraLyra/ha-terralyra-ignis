import json
import unittest
from fr_alert_review import inspect_detail, MAX_BYTES


def page(info):
    data = json.dumps({'alert_entity': {'infos': [info]}})
    return ('<script type="application/json" data-drupal-selector="drupal-settings-json">' + data + '</script>').encode()


class ReviewTests(unittest.TestCase):
    def test_preserves_unknown_and_markup(self):
        info = {'description': [{'value': '<img onerror="bad()">'}], 'unknown': [1, 2]}
        result = inspect_detail(page(info))['results'][0]
        self.assertEqual(result['source'], info)
        self.assertIsNone(result['active'])
        self.assertIsNone(result['is_test'])
        self.assertFalse(result['incident_id_verified'])

    def test_epoch_candidate_is_not_verified(self):
        result = inspect_detail(page({'effective': [{'value': '1785518130'}]}))['results'][0]
        self.assertEqual(result['epoch_seconds_candidates']['effective'], '2026-07-31T17:15:30+00:00')
        self.assertFalse(result['timestamp_semantics_verified'])

    def test_rejects_missing_duplicate_and_truncated_settings(self):
        valid = page({})
        for raw in (b'<html></html>', valid + valid, valid[:-9]):
            with self.subTest(raw=raw):
                with self.assertRaises(ValueError): inspect_detail(raw)

    def test_bound(self):
        with self.assertRaises(ValueError): inspect_detail(b'x' * (MAX_BYTES + 1))

    def test_bad_timestamp_never_guessed(self):
        for source in ('not-a-date', True, '1e9', '-1', '9'*100):
            result = inspect_detail(page({'effective': [{'value': source}]}))['results'][0]
            self.assertIn('invalid_epoch_candidate_effective', result['issues'])
            self.assertEqual(result['epoch_seconds_candidates'], {})

    def test_state_not_interpreted_as_active(self):
        self.assertIsNone(inspect_detail(page({'state': [{'value': '1'}]}))['results'][0]['active'])

    def test_explicit_exercise_level(self):
        info = {'level': [{'value': 'EXERCISE'}], 'headline': [{'value': 'original'}]}
        result = inspect_detail(page(info))['results'][0]
        self.assertTrue(result['is_test'])
        self.assertEqual(result['test_evidence'], 'level=EXERCISE')
        self.assertEqual(result['source'], info)

    def test_other_levels_and_words_do_not_guess(self):
        for level in ('TEST', 'ALERT_LVL_2', 'unknown', None):
            result = inspect_detail(page({'level': [{'value': level}],
                                         'headline': [{'value': 'Test street fire'}]}))['results'][0]
            self.assertIsNone(result['is_test'])
            self.assertIsNone(result['test_evidence'])

    def test_expiry_conflict_preserved(self):
        info = {k: [{'value': v}] for k, v in
                [('effective', '100'), ('onset', '101'), ('expires', '99')]}
        r = inspect_detail(page(info))['results'][0]
        self.assertIn('expires_before_effective', r['issues'])
        self.assertIn('expires_before_onset', r['issues'])
        self.assertEqual(r['source'], info)
        self.assertIsNone(r['active'])

    def test_local_candidate_offsets_and_dst(self):
        from datetime import datetime
        cases = [('2026-01-28T20:19:28+00:00', 'Europe/Paris', '2026-01-28T21:19:28+01:00'),
                 ('2026-07-31T17:15:30+00:00', 'Europe/Paris', '2026-07-31T19:15:30+02:00'),
                 ('2026-03-29T00:30:00+00:00', 'Europe/Paris', '2026-03-29T01:30:00+01:00'),
                 ('2026-03-29T01:30:00+00:00', 'Europe/Paris', '2026-03-29T03:30:00+02:00'),
                 ('2026-10-25T00:30:00+00:00', 'Europe/Paris', '2026-10-25T02:30:00+02:00'),
                 ('2026-10-25T01:30:00+00:00', 'Europe/Paris', '2026-10-25T02:30:00+01:00'),
                 ('2026-07-31T17:15:30+00:00', 'America/Martinique', '2026-07-31T13:15:30-04:00')]
        for utc, zone, expected in cases:
            with self.subTest(utc=utc, zone=zone):
                info = {'effective': [{'value': str(int(datetime.fromisoformat(utc).timestamp()))}],
                        'timezone': [{'value': zone}]}
                r = inspect_detail(page(info))['results'][0]
                self.assertEqual(r['local_time_candidates']['effective'], expected)
                self.assertFalse(r['timestamp_semantics_verified'])

    def test_bad_timezone_has_no_fallback(self):
        r = inspect_detail(page({'timezone': [{'value': 'Europe/France'}]}))['results'][0]
        self.assertEqual(r['local_time_candidates'], {})
        self.assertIn('missing_or_invalid_timezone', r['issues'])
