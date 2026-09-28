import json
import unittest
from fr_alert_listing import inspect_listing


def page(alerts):
    return ('<script data-drupal-selector="drupal-settings-json">'+
            json.dumps({'alert_entity': {'alerts': alerts}})+'</script>').encode()


class ListingTests(unittest.TestCase):
    def test_actual_is_not_active(self):
        r = inspect_listing(page([{'status': [{'value': 'Actual'}]}]))
        self.assertIsNone(r['results'][0]['active'])
        self.assertIsNone(r['results'][0]['is_test'])
        self.assertFalse(r['snapshot_complete'])

    def test_exercise_and_source_retention(self):
        a = {'status': [{'value': 'Exercice'}], 'reference': [{'value': 'raw'}]}
        r = inspect_listing(page([a]))['results'][0]
        self.assertTrue(r['is_test'])
        self.assertEqual(r['source'], a)

    def test_duplicates_retained(self):
        a = {'identifier': [{'value': 'same'}]}
        r = inspect_listing(page([a, a]))
        self.assertEqual(r['inspected_alerts'], 2)
        self.assertIn('duplicate_identifier', r['results'][1]['issues'])

    def test_empty_does_not_prove_no_warnings(self):
        self.assertFalse(inspect_listing(page([]))['snapshot_complete'])

    def test_invalid_or_truncated_input(self):
        for raw in (page([{}]*201), page([False]), page([])[:-9], b'x'*1048577):
            with self.subTest(size=len(raw)):
                with self.assertRaises(ValueError): inspect_listing(raw)

    def test_homepage_timezone_matches_detail_encoding(self):
        from fr_alert_review import review_infos
        info = {'timezone': {'0': {'value': 'Europe/Paris'}, 'translate': 'display only'},
                'effective': [{'value': '1785518130'}]}
        result = inspect_listing(page([{'infos': [info]}]))['results'][0]
        self.assertEqual(result['info_reviews'][0]['local_time_candidates']['effective'],
                         '2026-07-31T19:15:30+02:00')
        self.assertEqual(result['source']['infos'][0], info)
        detail = dict(info, timezone=[{'value': 'Europe/Paris'}])
        self.assertEqual(review_infos([detail])[0]['local_time_candidates'],
                         result['info_reviews'][0]['local_time_candidates'])

    def test_ambiguous_timezone_never_picks_first(self):
        for zone in ({'0': {'value': 'Europe/Paris'}, '1': {'value': 'UTC'}},
                     {'translate': 'Europe/Paris'}, {'0': False}):
            result = inspect_listing(page([{'infos': [{'timezone': zone}]}]))['results'][0]
            r = result['info_reviews'][0]
            self.assertIn('missing_or_invalid_timezone', r['issues'])
            self.assertEqual(r['local_time_candidates'], {})

    def test_bad_infos_do_not_drop_source_record(self):
        for infos in (None, [], [False], [{}]*21):
            result = inspect_listing(page([{'infos': infos}]))['results'][0]
            self.assertIn('missing_or_invalid_infos', result['issues'])
            self.assertEqual(result['source']['infos'], infos)
