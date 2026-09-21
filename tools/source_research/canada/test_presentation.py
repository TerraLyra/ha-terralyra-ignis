import unittest
from presentation import match_record, match_locations

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

    def test_malformed_metadata_preserved_without_crashing_or_certainty(self):
        feature = self.record(status={'unexpected': 'OC'})
        feature['properties'].update(percent_contained=True, fire_was_prescribed=[])
        result = match_record(feature, latitude=50, longitude=179.9, radius_km=1)
        self.assertEqual(result['stage_of_control'], 'unknown')
        self.assertIsNone(result['percent_contained'])
        self.assertEqual(result['prescribed_status'], 'unknown')
        self.assertEqual(result['metadata_warnings'], (
            'invalid_percent_contained', 'unknown_stage_of_control_status',
            'unknown_fire_was_prescribed'))
        self.assertEqual(result['raw_properties'], feature['properties'])
        self.assertTrue(result['inside_radius'])

    def test_containment_bounds_and_unknown_sentinel(self):
        for raw, expected in ((0, 0), (100, 100), (12.5, 12.5), (-1, None),
                              (None, None), (-2, None), (101, None),
                              ('50', None), (float('inf'), None), ([], None)):
            with self.subTest(raw=raw):
                feature = self.record(status='UC')
                feature['properties']['percent_contained'] = raw
                result = match_record(feature, latitude=50, longitude=179.9, radius_km=1)
                self.assertEqual(result['percent_contained'], expected)
                self.assertEqual(result['current_activity'], 'not_established')

    def location(self, identity, lon=179.9, enabled=True):
        return dict(id=identity, name=identity, latitude=50, longitude=lon,
                    radius_km=20, enabled=enabled)

    def test_multiple_places_select_nearest_and_preserve_all_matches(self):
        places = [self.location('farther', -179.9), self.location('canada'),
                  self.location('home', 0), self.location('disabled', enabled=False)]
        result = match_locations(self.record(), places)
        self.assertEqual(result['distance_reference_id'], 'canada')
        self.assertEqual(result['distance_km'], 0)
        self.assertEqual([m['location_id'] for m in result['location_matches']],
                         ['canada', 'farther'])
        self.assertEqual(result, match_locations(self.record(), reversed(places)))

    def test_no_home_fallback_and_location_removal(self):
        feature = self.record()
        for places in ([], [self.location('home', 0)],
                       [self.location('canada', enabled=False)]):
            self.assertIsNone(match_locations(feature, places))
        self.assertIsNotNone(match_locations(feature, [self.location('canada')]))
        self.assertIsNone(match_locations(feature, []))

    def test_equal_distances_stable_and_ambiguous_locations_rejected(self):
        result = match_locations(self.record(), [self.location('b'), self.location('a')])
        self.assertEqual(result['distance_reference_id'], 'a')
        with self.assertRaises(ValueError):
            match_locations(self.record(), [self.location('a'), self.location('a')])
        with self.assertRaises(ValueError):
            match_locations(self.record(), [self.location('a', enabled='false')])
