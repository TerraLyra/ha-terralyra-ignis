import unittest
from presentation import match_record

class MatchingTests(unittest.TestCase):
    def record(self,lon=179.9,lat=50,status='NEW_CODE'):
        return dict(properties=dict(national_fire_id='synthetic',agency_code='BC',
            stage_of_control_status=status,fire_was_prescribed=-1,
            situation_report_date='2020-01-01T00:00:00Z',status_date='2020-01-01T00:00:00Z',
            record_start='2026-01-01T00:00:00Z',record_end='2026-12-31T23:59:59Z'),
            geometry=dict(type='Point',coordinates=[lon,lat]))

    def test_dateline_and_location_relative_distance(self):
        result=match_record(self.record(),latitude=50,longitude=-179.9,radius_km=20)
        self.assertTrue(result['inside_radius'])
        self.assertGreater(result['distance_km'],14)
        self.assertLess(result['distance_km'],15)
        other=match_record(self.record(),latitude=0,longitude=0,radius_km=20)
        self.assertFalse(other['inside_radius'])

    def test_unknown_code_preserved_and_old_report_not_removed(self):
        result=match_record(self.record(),latitude=50,longitude=179.9,radius_km=1)
        self.assertEqual(result['stage_of_control'],'unknown')
        self.assertEqual(result['source_status'],'NEW_CODE')
        self.assertEqual(result['prescribed_status'],'not_reported')
        self.assertEqual(result['current_activity'],'not_established')
        self.assertTrue(result['inside_radius'])

    def test_extinguished_is_source_status_not_automatic_all_clear(self):
        result=match_record(self.record(status='EX'),latitude=50,longitude=179.9,radius_km=1)
        self.assertEqual(result['stage_of_control'],'extinguished')
        self.assertEqual(result['current_activity'],'not_established')

    def test_invalid_radius(self):
        for radius in (0,-1,float('nan'),True):
            with self.subTest(radius=radius),self.assertRaises(ValueError):
                match_record(self.record(),latitude=50,longitude=179.9,radius_km=radius)
