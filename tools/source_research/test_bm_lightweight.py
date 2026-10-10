"""Model-free runtime matcher regressions with literal, synthetic source text."""
import unittest
from test_bm_satellite_context import BMTownReport
from _bm_context_test.bm_lightweight import lightweight_report

class LightweightTests(unittest.TestCase):
    def run_text(self, text, names=None, **extra):
        notice=dict(url='https://www.katasztrofavedelem.hu/modules/vesz/esemeny/1',published_at='2026-10-07T12:00:00+00:00',title=text,description='',**extra)
        return lightweight_report(notice,names or {'geonames:1':'Hejőbába'})

    def test_locative_and_nearby(self):
        for text in ['Melléképület égett Hejőbábán','Hejőbába határában ég a nádas','Hejőbába közelében tűz keletkezett']:
            report,evidence=self.run_text(text)
            self.assertEqual(report.event_settlement_ids,frozenset({'geonames:1'}))
            self.assertEqual(text[evidence[0]['start']:evidence[0]['end']],evidence[0]['text'])

    def test_responder_direction_street_negation_and_accident(self):
        for text in ['A hejőbábai tűzoltók oltanak, ég a ház.', 'Hejőbába felé ég a nádas', 'Hejőbábán nem ég a ház', 'Hejőbábán baleset történt. Máshol ég egy autó.', 'Hejőbábán gyakorlaton kigyulladt egy autó', 'Hejőbába utcában ég egy ház', 'Hejőbába tűzoltóság szerint ég a nádas']:
            self.assertFalse(self.run_text(text)[0].event_settlement_ids,text)

    def test_ambiguous_names_and_truncated_text(self):
        self.assertFalse(self.run_text('Hejőbábán ég a ház',{'a':'Hejőbába','b':'Hejőbába'})[0].fire_report)
        self.assertFalse(self.run_text('Hejőbábán ég a ház',description_status='truncated')[0].fire_report)

    def test_no_model_needed_and_original_text_retained(self):
        text='Szegeden kigyulladt egy épület'
        report,_=self.run_text(text,{'geonames:2':'Szeged'})
        self.assertEqual(report.title,text)
        self.assertTrue(report.fire_report)

    def test_vegetation_adjective_is_not_bokros_settlement(self):
        names = {'b': 'Bokros', 'f': 'Balatonfűzfő'}
        for text in ('A bokros terület ég.',
                     'Árokba borult egy autó Balatonfűzfőnél. A tűzoltók megtisztítják a bokros területet.'):
            report, evidence = self.run_text(text, names)
            self.assertFalse(report.fire_report)
            self.assertFalse(evidence)
        report, _ = self.run_text('Bokros közelében ég a nádas.', names)
        self.assertEqual(report.event_settlement_ids, frozenset({'b'}))
