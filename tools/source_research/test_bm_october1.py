"""BM OKF RSS 92462/92453 excerpts: offline candidates, never coordinates."""
import unittest
from bm_hu_gazetteer import load_review_places
from bm_location_candidates import review_locations


class OctoberReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.places = load_review_places()

    def review(self, title, description):
        result = review_locations(title, description, '', self.places)
        self.assertFalse(result.incident_location_verified)
        self.assertEqual(result.description, description)
        for mention in result.mentions:
            text = title if mention.field == 'title' else description
            self.assertEqual(text[mention.start:mention.end], mention.evidence)
            for hint in mention.context_hints:
                self.assertEqual(text[hint.start:hint.end], hint.evidence)
        return result

    def test_tiszadob_event_and_four_responder_towns(self):
        result = self.review('Kigyulladt a száraz fű Tiszadobon',
            'Kigyulladt a száraz fű Tiszadobon, az Árpád utca közelében. '
            'A tiszaújvárosi és a hajdúnánási hivatásos, valamint a tiszavasvári '
            'önkormányzati és tiszadobi önkéntes tűzoltók dolgoznak a lángok megfékezésén.')
        self.assertEqual({m.settlement_name for m in result.mentions},
                         {'Tiszadob', 'Tiszaújváros', 'Hajdúnánás', 'Tiszavasvári'})
        for mention in result.mentions:
            if mention.evidence == 'Tiszadobon':
                self.assertEqual(mention.context_hints, ())
            else:
                self.assertIn('responder_list_reference', {h.kind for h in mention.context_hints})

    def test_szeged_is_distinct_from_compound_street(self):
        result = self.review('Tűz van Szegeden',
            'Tűz keletkezett Szegeden, a Zsámbok-Réti soron, egy üzem területén.')
        for mention in result.mentions:
            if mention.settlement_name == 'Szeged':
                self.assertEqual(mention.context_hints, ())
            elif mention.settlement_name == 'Zsámbok':
                self.assertEqual(mention.context_hints[0].kind, 'street_name_reference')
                self.assertEqual(mention.context_hints[0].evidence, 'Zsámbok-Réti soron')
        self.assertIn('Zsámbok', {m.settlement_name for m in result.mentions})

    def test_standalone_town_and_sentence_boundaries_remain_unmarked(self):
        for text in ('Zsámbok közelében.', 'Zsámbok. Réti soron.',
                     'Zsámbok-\nRéti soron.', 'Zsámbok-Réti sorozat.',
                     'Tiszadobon, valamint Hajdúnánás közelében tűz van.'):
            with self.subTest(text=text):
                result = self.review(text, '')
                self.assertTrue(result.mentions)
                self.assertTrue(all(not m.context_hints for m in result.mentions))
