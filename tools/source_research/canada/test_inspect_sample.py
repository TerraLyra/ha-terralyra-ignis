import unittest
from inspect_sample import inspect


class InspectionTests(unittest.TestCase):
    def test_truncated_and_unknown_counts(self):
        for matched in (3, 'unknown', True):
            self.assertFalse(inspect(dict(type='FeatureCollection', features=[], numberMatched=matched, numberReturned=0))['response_count_complete'])

    def test_empty_response_is_not_national_all_clear(self):
        result = inspect(dict(type='FeatureCollection', features=[], numberMatched=0, numberReturned=0))
        self.assertTrue(result['response_count_complete'])
        self.assertEqual(result['national_coverage'], 'not_established')

    def test_unknown_percentage_and_naive_time_are_visible(self):
        record = dict(properties=dict(national_fire_id='synthetic', percent_contained=-1,
            situation_report_date='2026-01-01T00:00:00', status_date='2026-01-01T00:00:00Z',
            record_start='2026-01-01T00:00:00Z', record_end='2026-01-01T00:00:00Z'))
        result = inspect(dict(type='FeatureCollection', features=[record,record], numberMatched=2, numberReturned=2))
        self.assertIn('0:situation_report_date:invalid_or_naive', result['issues'])
        self.assertIn('0:percent_contained:unknown_sentinel', result['issues'])
        self.assertIn('0:invalid_validity_interval', result['issues'])
        self.assertIn('1:duplicate_national_fire_id', result['issues'])


if __name__ == '__main__':
    unittest.main()
