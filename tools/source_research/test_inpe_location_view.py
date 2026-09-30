from dataclasses import replace
from unittest import TestCase
from inpe_snapshot import Snapshot
from inpe_location_view import Location, distance_km, location_report, render_preview
from test_inpe_snapshot import record, NOW


class LocationViewTests(TestCase):
    def snapshot(self, *records):
        return Snapshot(('AC','AM'),records or (record(),),NOW)

    def test_explicit_location_reference(self):
        near=location_report(self.snapshot(),Location('Chosen',-10,-50,1))
        far=location_report(self.snapshot(),Location('Elsewhere',0,0,1))
        self.assertEqual(near['events'][0]['distance_km'],0)
        self.assertEqual(far['events'],[])
        self.assertFalse(far['complete'])
        self.assertIn('nem igazolja',far['empty_message'])

    def test_dateline_and_antipodes(self):
        self.assertAlmostEqual(distance_km(0,179.9,0,-179.9),22.239,places=2)
        self.assertAlmostEqual(distance_km(0,0,0,180),20015.114,places=2)

    def test_invalid_location(self):
        for location in (Location('',0,0,1),Location('x',91,0,1),Location('x',0,181,1),
                         Location('x',0,0,0),Location('x',0,0,float('nan')),Location('x',True,0,1)):
            with self.subTest(location=location),self.assertRaises(ValueError): location_report(self.snapshot(),location)

    def test_stable_order(self):
        a=record(); b=replace(a,source_id=2)
        result=location_report(self.snapshot(b,a),Location('x',-10,-50,1))
        self.assertEqual([e['source_id'] for e in result['events']],[1,2])

    def test_html_escaped_and_unknown_status_retained(self):
        event=replace(record(),municipality='<script>alert(1)</script>',status='<img onerror=x>',area_ha=None)
        html=render_preview(self.snapshot(event),Location('<img>',-10,-50,1))
        self.assertNotIn('<script>',html)
        self.assertNotIn('<img',html)
        self.assertIn('&lt;img onerror=x&gt;',html)
        self.assertIn('Ismeretlen szolgáltatói státusz',html)
        self.assertIn('Nincs adat',html)
        self.assertIn('CC BY-SA 4.0',html)
        self.assertIn('nem a tűz teljes területére',html)
