import json
import unittest
from spain_cyl_preview import render


class PreviewTests(unittest.TestCase):
    def test_untrusted_text_is_escaped_and_conflict_retained(self):
        row = dict(termino_municipal='<script>alert(1)</script>', situacion_actual='CONTROLADO',
                   fecha_extinguido='2026-09-17', hora_extinguido='14:03')
        html = render(json.dumps(dict(total_count=20, results=[row])).encode())
        self.assertNotIn('<script>', html)
        self.assertIn('&lt;script&gt;', html)
        self.assertIn('CONTROLADO', html)
        self.assertIn('14:03', html)
        self.assertIn('ellentmondhat', html)
        self.assertIn('Nem élő állapot', html)
        self.assertIn('CC BY 4.0', html)

    def test_no_incident_notice_is_not_a_fire_title(self):
        html = render(json.dumps(dict(total_count=1, results=[dict(termino_municipal='SIN INCIDENCIAS')])).encode())
        self.assertIn('Nincs esemény a jelentéssor szerint', html)
