"""Synthetic context clues; all candidate evidence remains review-only."""
import unittest
from bm_location_candidates import Settlement, review_locations

PLACES = (Settlement('k','Komárom'),Settlement('e','Esztergom'),
          Settlement('t','Tatabánya',('tatabányai',)),
          Settlement('v','Vértesszőlős',('vértesszőlősi',)))

class ContextTests(unittest.TestCase):
    def result(self, text):
        return review_locations('', text, '', PLACES)

    def test_compound_county_keeps_both_mentions_with_exact_context(self):
        for dash in ('-', '–'):
            text = f'A Komárom{dash}Esztergom vármegyei szolgálat.'
            result = self.result(text)
            self.assertEqual(len(result.mentions), 2)
            for mention in result.mentions:
                hint, = mention.context_hints
                self.assertEqual(hint.kind, 'county_name')
                self.assertEqual(text[hint.start:hint.end], hint.evidence)
            self.assertFalse(result.incident_location_verified)

    def test_direct_responder_reference(self):
        result = self.result('A tatabányai hivatásos tűzoltók megérkeztek.')
        hint, = result.mentions[0].context_hints
        self.assertEqual(hint.kind, 'responder_reference')
        self.assertEqual(hint.evidence, 'tatabányai hivatásos tűzoltók')

    def test_event_adjective_does_not_become_responder(self):
        result = self.result('Egy vértesszőlősi házban tűz keletkezett.')
        self.assertEqual(result.mentions[0].context_hints, ())
        self.assertFalse(result.incident_location_verified)

    def test_separate_city_and_county_mentions(self):
        result = self.result('Komárom közelében, Komárom-Esztergom vármegyében.')
        self.assertEqual(result.mentions[0].context_hints, ())
        self.assertEqual(result.mentions[1].context_hints[0].kind, 'county_name')

    def test_no_cross_sentence_responder_hint(self):
        self.assertEqual(self.result('Tatabányai. Tűzoltók érkeztek.').mentions[0].context_hints, ())

    def test_unknown_context_stays_unknown(self):
        result = self.result('Nem Esztergom a helyszín.')
        self.assertEqual(result.mentions[0].context_hints, ())
        self.assertEqual(result.status, 'requires_review')
