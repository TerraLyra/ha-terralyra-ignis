import json
import unittest
from bm_location_candidates import Settlement
from bm_review_sample import evaluate_sample, MAX_BYTES


class SampleTests(unittest.TestCase):
    places = (Settlement('s', 'Szeged', ('Szegeden',)),)
    record = {'title': 'Tűz Szegeden', 'description': '', 'source_url': 'https://example.invalid/1'}

    def evaluate(self, data):
        return evaluate_sample(json.dumps(data).encode(), self.places)

    def test_repeatable_output_and_preserved_evidence(self):
        result = self.evaluate([self.record])
        self.assertEqual(result, self.evaluate([self.record]))
        self.assertEqual(result['results'][0]['review']['title'], self.record['title'])
        self.assertFalse(result['accuracy_assessed'])
        self.assertFalse(result['results'][0]['review']['incident_location_verified'])

    def test_duplicates_not_counted_as_independent_content(self):
        result = self.evaluate([self.record, self.record])
        self.assertEqual(result['distinct_content_count'], 1)
        self.assertTrue(result['results'][1]['duplicate_in_sample'])

    def test_revised_description_is_distinct_content_not_proof_of_new_event(self):
        result = self.evaluate([self.record, {**self.record, 'description': 'Frissítés'}])
        self.assertEqual(result['distinct_content_count'], 2)

    def test_invalid_inputs_and_bounds(self):
        for data in ({}, [None], [{}], [self.record]*101,
                     [{**self.record, 'input_truncated': 'false'}]):
            with self.assertRaises(ValueError):
                self.evaluate(data)
        with self.assertRaises(ValueError):
            evaluate_sample(b' '*(MAX_BYTES+1), self.places)

    def test_truncated_and_empty(self):
        self.assertEqual(self.evaluate([])['report_count'], 0)
        result = self.evaluate([{**self.record, 'input_truncated': True}])
        self.assertEqual(result['results'][0]['review']['mentions'], ())
