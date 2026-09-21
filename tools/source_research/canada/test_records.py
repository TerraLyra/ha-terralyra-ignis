import unittest
from records import project_record

class RecordTests(unittest.TestCase):
    def test_preserve_unknown_and_time_meanings(self):
        p=dict(national_fire_id='2020_QC_example',agency_code='QC',percent_contained=-1,
            stage_of_control_status='OC',situation_report_date='2020-01-01T00:00:00Z',
            status_date='2020-02-01T00:00:00Z',record_start='2026-01-01T00:00:00Z',
            record_end='2026-12-31T23:59:59Z')
        f=dict(properties=p,geometry=dict(type='Point',coordinates=[-71,48]))
        record=project_record(f)
        self.assertIsNone(record['percent_contained'])
        self.assertEqual(record['raw_properties']['percent_contained'],-1)
        self.assertTrue(record['source_times']['status_date'].startswith('2020'))
        self.assertTrue(record['source_times']['record_start'].startswith('2026'))
        record['raw_properties']['percent_contained']=25
        self.assertEqual(p['percent_contained'],-1)
