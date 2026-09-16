"""Synthetic ACT research-reader tests; no live incident data."""
import unittest
from act_feed import inspect_feed, InvalidFeed


def feed(item=''):
    return ('<rss version="2.0"><channel>' + item + '</channel></rss>').encode()


class FeedTests(unittest.TestCase):
    def test_preserves_distinct_raw_times_and_statuses(self):
        result = inspect_feed(feed('<item><type>AMBULANCE RESPONSE</type>'
            '<pubDate>2026-09-16 23:27 AEST</pubDate>'
            '<description>Updated: 16 Sep 2026 22:54:31.2</description>'
            '<resourceStatus>On Scene</resourceStatus>'
            '<controlStatus>Not Applicable</controlStatus></item>'))
        fields = dict(result[0].fields)
        self.assertNotEqual(fields['pubDate'], fields['description'])
        self.assertEqual(fields['type'], 'AMBULANCE RESPONSE')
        self.assertEqual(fields['controlStatus'], 'Not Applicable')

    def test_no_date_or_fire_inference(self):
        result = inspect_feed(feed('<item><title>TEST ONLY</title>'
                                  '<type>GRASS AND BUSH FIRE</type></item>'))
        self.assertEqual(len(result[0].fields), 2)
        self.assertEqual(dict(result[0].fields)['title'], 'TEST ONLY')

    def test_georss_namespace_and_coordinate_order_preserved(self):
        result = inspect_feed(feed('<item><g:point xmlns:g="http://www.georss.org/georss">'
                                  '-35 149</g:point></item>'))
        self.assertEqual(result[0].fields, (('{http://www.georss.org/georss}point', '-35 149'),))

    def test_valid_empty_feed(self):
        self.assertEqual(inspect_feed(feed()), ())

    def test_bad_envelopes_and_structure(self):
        for raw in [b'', b'<html/>', b'<rss version="2.0"/>',
                    feed('<item/>'), feed('<item><type>A</type><type>B</type></item>'),
                    feed('<item><a><b/></a></item>'), feed()[:-1],
                    b'<rss version="2.0"><channel/><channel/></rss>']:
            with self.subTest(raw=raw), self.assertRaises(InvalidFeed):
                inspect_feed(raw)

    def test_hostile_xml(self):
        for raw in [b'<!DOCTYPE rss [<!ENTITY x "boom">]>' + feed(),
                    feed().decode().encode('utf-16'), b'\xff',
                    feed('<item>' + '<a>'*100 + '</a>'*100 + '</item>')]:
            with self.subTest(raw=raw), self.assertRaises(InvalidFeed):
                inspect_feed(raw)

    def test_limits(self):
        with self.assertRaises(InvalidFeed):
            inspect_feed(feed(), max_bytes=2)
        with self.assertRaises(InvalidFeed):
            inspect_feed(feed('<item><a/></item>'*2), max_items=1)
        for value in [True, 0, -1, 1.5]:
            with self.assertRaises(ValueError):
                inspect_feed(feed(), max_items=value)


if __name__ == '__main__':
    unittest.main()
