import json
import unittest
from fr_alert_changes import compare_samples


def sample(rows):
    return ('<script data-drupal-selector="drupal-settings-json">' +
            json.dumps({'alert_entity': {'alerts': rows}}) + '</script>').encode()


def row(identifier, text='original'):
    return {'identifier': [{'value': identifier}], 'note': text}


class ChangeTests(unittest.TestCase):
    def test_disappearance_is_not_cancellation(self):
        r = compare_samples(sample([row('a')]), sample([]))
        self.assertEqual(r['changes'][0]['kind'], 'not_observed_in_second_sample')
        self.assertEqual(r['changes'][0]['before'], [row('a')])
        self.assertFalse(r['lifecycle_verified'])

    def test_content_change_preserves_versions(self):
        r = compare_samples(sample([row('a')]), sample([row('a', 'new')]))
        self.assertEqual(r['changes'][0]['kind'], 'source_changed')
        self.assertEqual(r['changes'][0]['after'][0]['note'], 'new')

    def test_order_does_not_matter(self):
        r = compare_samples(sample([row('b'), row('a')]), sample([row('a'), row('b')]))
        self.assertTrue(all(c['kind'] == 'unchanged' for c in r['changes']))

    def test_duplicate_is_never_merged(self):
        r = compare_samples(sample([row('a'), row('a')]), sample([row('a')]))
        self.assertEqual(r['changes'][0]['kind'], 'ambiguous_duplicate')
        self.assertEqual(len(r['changes'][0]['before']), 2)

    def test_missing_identity_and_new_record(self):
        r = compare_samples(sample([{}]), sample([row('new')]))
        self.assertEqual(r['unidentified_row_indexes'], [[0], []])
        self.assertEqual(r['changes'][0]['kind'], 'newly_observed')

    def test_failed_input_is_not_empty_snapshot(self):
        with self.assertRaises(ValueError):
            compare_samples(sample([row('a')]), b'<html>error</html>')
