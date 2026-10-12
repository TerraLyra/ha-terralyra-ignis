"""Synthetic offline fixtures; no upstream event pages or HA state."""
import unittest
from tasalert_kml import parse_kml, timestamp


def sample(kind='incident', coords='147.5,-42.8', extra='', identifier='one'):
    point = f'<MultiGeometry><Point><coordinates>{coords}</coordinates></Point></MultiGeometry>' if coords is not None else '<Polygon/>'
    return f'<kml xmlns="http://www.opengis.net/kml/2.2"><Document><Placemark id="{identifier}"><name>Example</name><ExtendedData><Data name="feedType"><value>{kind}</value></Data>{extra}</ExtendedData>{point}</Placemark></Document></kml>'.encode()


class TasAlertTests(unittest.TestCase):
    def test_point_order_and_unknown_status_preserved(self):
        extra='<Data name="status"><value>Unreviewed status</value></Data><Data name="type"><value>Fuel Reduction Burn</value></Data>'
        record=parse_kml(sample(extra=extra))[0]
        self.assertEqual(record['point'], {'latitude':-42.8,'longitude':147.5})
        self.assertEqual(record['fields']['status'],'Unreviewed status')
        self.assertEqual(record['fields']['type'],'Fuel Reduction Burn')

    def test_area_never_manufactures_point(self):
        record=parse_kml(sample(kind='burnt-area',coords=None))[0]
        self.assertIsNone(record['point'])
        self.assertTrue(record['has_polygon'])
        with self.assertRaises(ValueError):parse_kml(sample(coords=None))

    def test_invalid_coordinates(self):
        for value in ('NaN,0','181,0','0,91','147,42 148,43','1','1,2,3,4'):
            with self.subTest(value=value), self.assertRaises(ValueError):parse_kml(sample(coords=value))

    def test_offset_required_and_retained(self):
        for value in ('2026-07-01T12:00:00+10:00','2026-01-01T12:00:00+11:00','2026-04-05T02:30:00+11:00','2026-04-05T02:30:00+10:00'):
            self.assertEqual(timestamp(value),value)
        for value in ('2026-10-04T02:30:00','invalid'):
            with self.assertRaises(ValueError):timestamp(value)

    def test_duplicates_and_unsafe_xml(self):
        raw=sample(); text=raw.decode(); mark=text[text.index('<Placemark'):text.index('</Placemark>')+12]
        with self.assertRaises(ValueError):parse_kml(text.replace('</Document>',mark+'</Document>').encode())
        with self.assertRaises(ValueError):parse_kml(b'<!DOCTYPE kml>'+raw)
        with self.assertRaises(ValueError):parse_kml(sample(identifier=''))
        with self.assertRaises(ValueError):parse_kml(sample(kind='unknown'))

    def test_unsafe_links(self):
        for url in ('javascript:bad','https://other.example/','https://user@alert.tas.gov.au/'):
            with self.assertRaises(ValueError):parse_kml(sample(extra=f'<Data name="url"><value>{url}</value></Data>'))

    def test_empty_snapshot_is_not_a_safety_claim(self):
        self.assertEqual(parse_kml(b'<kml xmlns="http://www.opengis.net/kml/2.2"/>'),[])
