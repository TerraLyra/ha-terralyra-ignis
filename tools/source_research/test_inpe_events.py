"""Synthetic INPE fixtures; no republished source records or live requests."""
from unittest import TestCase
from unittest.mock import patch
from inpe_events import inspect_events, InvalidEvents, NS


def event(identifier='1', coords='-50,-10,0', category='Incêndio'):
    return f'''<Folder><name>Evento {identifier} – {category}</name>
    <Folder><name>Focos</name><Placemark><Point><coordinates>1,2</coordinates></Point></Placemark></Folder>
    <Placemark><Polygon/><description>polygon</description></Placemark>
    <Placemark><Point><coordinates>{coords}</coordinates></Point>
    <description>&lt;table&gt;Último foco: 2026-09-29 17:47:00&lt;/table&gt;</description></Placemark></Folder>'''


def wrap(body):
    return f'<kml xmlns="{NS[1:-1]}"><Document>{body}</Document></kml>'.encode()


class InpeTests(TestCase):
    def test_one_event_not_each_point_or_polygon(self):
        records = inspect_events(wrap(event()), collection='active')
        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual((record.longitude, record.latitude), (-50, -10))
        self.assertTrue(record.geometry_present)
        self.assertTrue(record.provisional)
        self.assertIsNone(record.observed_at)
        self.assertIn('<table>', record.description_raw)

    def test_unknown_category_and_observation_retained(self):
        r = inspect_events(wrap(event(category='Future category')), collection='observation')[0]
        self.assertEqual(r.category, 'Future category')
        self.assertEqual(r.collection, 'observation')

    def test_invalid_coordinates(self):
        for c in ('181,0', '0,91', 'nan,0', '0,inf', '0,0,nan', '0', '1,2 3,4', 'x,2'):
            with self.subTest(c=c), self.assertRaises(InvalidEvents):
                inspect_events(wrap(event(coords=c)), collection='active')

    def test_duplicate_ids_fail_whole_snapshot(self):
        with self.assertRaises(InvalidEvents):
            inspect_events(wrap(event()+event()), collection='active')

    def test_duplicate_point_and_text_rejected(self):
        for content in (event().replace('<Polygon/>', '<Point><coordinates>1,2</coordinates></Point>'),
                        event().replace('<name>Evento', '<name>extra</name><name>Evento')):
            with self.assertRaises(InvalidEvents): inspect_events(wrap(content), collection='active')

    def test_xml_errors_and_linked_inventory(self):
        for content in (b'<broken>', b'<html/>', wrap(''), wrap('<NetworkLink/>'),
                        b'<!DOCTYPE kml [<!ENTITY x "a">]>'+wrap(event()),
                        wrap(event())+b'\x00', b'\xff'):
            with self.subTest(content=content[:30]), self.assertRaises(InvalidEvents):
                inspect_events(content, collection='active')

    def test_size_count_depth_limits(self):
        with patch('inpe_events.MAX_BYTES', 10), self.assertRaises(InvalidEvents):
            inspect_events(wrap(event()), collection='active')
        with patch('inpe_events.MAX_EVENTS', 1), self.assertRaises(InvalidEvents):
            inspect_events(wrap(event()+event('2')), collection='active')
        with self.assertRaises(InvalidEvents):
            inspect_events(wrap('<Folder>'*33+event()+'</Folder>'*33), collection='active')

    def test_collection_required(self):
        with self.assertRaises(InvalidEvents): inspect_events(wrap(event()), collection='extinguished')
