"""Regression for reviewed RSS 92280 forms, using packaged place records."""
import unittest
from bm_bundled_places import load_hungarian_places
from bm_hu_gazetteer import load_review_places
from bm_location_candidates import review_locations


class ReviewedErdTests(unittest.TestCase):
    def test_location_and_responder_stay_separate_with_both_databases(self):
        title = 'Kigyulladt egy garázs Érden'
        description = 'Tűz keletkezett egy garázsban, Érden, a Gyopár utcában. A törökbálinti hivatásos tűzoltók oltják a lángokat.'
        for loader in (load_hungarian_places, load_review_places):
            with self.subTest(loader=loader.__name__):
                result = review_locations(title, description, '', loader())
                erd = [m for m in result.mentions if m.settlement_name == 'Érd']
                self.assertEqual(len(erd), 2)
                self.assertTrue(all(m.evidence == 'Érden' and not m.context_hints for m in erd))
                responder, = [m for m in result.mentions if m.settlement_name == 'Törökbálint']
                self.assertEqual(responder.context_hints[0].kind, 'responder_reference')
                for mention in result.mentions:
                    self.assertEqual({'title': title, 'description': description}[mention.field][mention.start:mention.end], mention.evidence)
                self.assertFalse(result.incident_location_verified)
                self.assertTrue(result.multiple_candidates)

    def test_word_boundaries_do_not_match_unrelated_words(self):
        result = review_locations('Érdemes érdemben válaszolni.', '', '', load_review_places())
        self.assertFalse(any(m.settlement_name == 'Érd' for m in result.mentions))

    def test_adjective_alone_is_not_a_responder_or_verified_location(self):
        result = review_locations('Egy érdi és törökbálinti épület.', '', '', load_review_places())
        self.assertEqual({m.settlement_name for m in result.mentions}, {'Érd', 'Törökbálint'})
        self.assertTrue(all(not m.context_hints for m in result.mentions))
        self.assertFalse(result.incident_location_verified)
