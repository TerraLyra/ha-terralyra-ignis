import copy
from datetime import datetime, timezone
import unittest

from nifc_records import normalize_page


def sample():
    return dict(objectIdFieldName='OBJECTID', geometryType='esriGeometryPoint',
                spatialReference={'wkid': 4326}, exceededTransferLimit=True,
                features=[dict(attributes=dict(
                    OBJECTID=1, IrwinID='{12345678-1234-1234-1234-123456789ABC}',
                    IncidentTypeCategory='WF', FireDiscoveryDateTime=1001,
                    ModifiedOnDateTime_dt=2002), geometry=dict(x=-120, y=40))])


class RecordTests(unittest.TestCase):
    def test_identity_coordinates_and_distinct_utc_times(self):
        record, = normalize_page(sample())
        self.assertEqual(record.irwin_id, '12345678-1234-1234-1234-123456789abc')
        self.assertEqual((record.longitude, record.latitude), (-120, 40))
        self.assertEqual(record.discovered_at, datetime(1970, 1, 1, 0, 0, 1, 1000, tzinfo=timezone.utc))
        self.assertEqual(record.modified_at.microsecond, 2000)

    def test_categories_are_separate(self):
        for raw, expected in [('WF', 'wildfire'), ('RX', 'prescribed_fire'), ('CX', 'incident_complex')]:
            page = sample(); page['features'][0]['attributes']['IncidentTypeCategory'] = raw
            self.assertEqual(normalize_page(page)[0].category, expected)

    def test_missing_values_have_no_fallback(self):
        page = sample(); feature = page['features'][0]
        feature.pop('geometry'); feature['attributes'].pop('FireDiscoveryDateTime')
        feature['attributes']['ModifiedOnDateTime_dt'] = None
        record, = normalize_page(page)
        self.assertIsNone(record.longitude); self.assertIsNone(record.latitude)
        self.assertIsNone(record.discovered_at); self.assertIsNone(record.modified_at)

    def test_bad_dates_reject_page(self):
        for value in (True, '1000', 1.5, 10**30):
            for field in ('FireDiscoveryDateTime', 'ModifiedOnDateTime_dt'):
                page = sample(); page['features'][0]['attributes'][field] = value
                with self.subTest(value=value, field=field), self.assertRaises(ValueError):
                    normalize_page(page)

    def test_bad_coordinates_are_not_swapped_or_clamped(self):
        for geometry in ({'x': True, 'y': 40}, {'x': -120, 'y': 91},
                         {'x': 181, 'y': 40}, {'x': float('nan'), 'y': 40},
                         {'x': 0, 'y': float('inf')}, {'x': '0', 'y': 0}, {},
                         {'x': 0, 'y': 0, 'spatialReference': {'wkid': 4269}}):
            page = sample(); page['features'][0]['geometry'] = geometry
            with self.subTest(geometry=geometry), self.assertRaises(ValueError): normalize_page(page)

    def test_bad_identity_and_unknown_category(self):
        for field, values in [('IrwinID', [None, '', '123', '00000000-0000-0000-0000-000000000000']),
                              ('IncidentTypeCategory', [None, '', 'OTHER', [], 'wf'])]:
            for value in values:
                page = sample(); page['features'][0]['attributes'][field] = value
                with self.subTest(field=field, value=value), self.assertRaises(ValueError): normalize_page(page)

    def test_duplicate_identity_with_different_object_ids(self):
        page = sample(); other = copy.deepcopy(page['features'][0])
        other['attributes']['OBJECTID'] = 2
        other['attributes']['IrwinID'] = '12345678-1234-1234-1234-123456789abc'
        page['features'].append(other)
        with self.assertRaises(ValueError): normalize_page(page)

    def test_envelope_validation_cannot_be_skipped(self):
        page = sample(); page['spatialReference']['wkid'] = 4269
        with self.assertRaises(ValueError): normalize_page(page)

    def test_input_is_unchanged(self):
        page = sample(); original = copy.deepcopy(page)
        normalize_page(page)
        self.assertEqual(page, original)
