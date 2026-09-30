"""Observed September 30 inflections retain event/responder distinctions."""
import unittest

from bm_hu_gazetteer import load_review_places
from bm_location_candidates import review_locations


class September30Review(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.places = load_review_places()

    def review(self, title, description):
        result = review_locations(title, description, '', self.places)
        self.assertEqual(result.title, title)
        self.assertEqual(result.description, description)
        self.assertFalse(result.incident_location_verified)
        return result

    def test_sojtor_and_shared_responder_noun(self):
        result = self.review(
            'Tűz volt egy söjtöri családi ház pincéjében',
            'Tűz keletkezett Söjtörön, a Deák Ferenc utcában. '
            'A zalaegerszegi és a pacsai hivatásos tűzoltók érkeztek a helyszínre.',
        )
        self.assertEqual({m.settlement_name for m in result.mentions},
                         {'Söjtör', 'Zalaegerszeg', 'Pacsa'})
        for mention in result.mentions:
            hints = {h.kind for h in mention.context_hints}
            if mention.settlement_name == 'Söjtör':
                self.assertFalse(hints)
            else:
                self.assertIn('responder_list_reference', hints)

    def test_same_town_as_event_and_responder(self):
        result = self.review(
            'Kigyulladt egy ház Tiszaföldváron',
            'Tűz keletkezett Tiszaföldváron. A lángokat eloltották a '
            'kunszentmártoni hivatásos és a tiszaföldvári önkormányzati tűzoltók.',
        )
        self.assertEqual({m.settlement_name for m in result.mentions},
                         {'Tiszaföldvár', 'Kunszentmárton'})
        for mention in result.mentions:
            hints = {h.kind for h in mention.context_hints}
            if mention.evidence == 'Tiszaföldváron':
                self.assertFalse(hints)
            else:
                self.assertIn('responder_list_reference', hints)

    def test_adjective_alone_is_not_responder(self):
        result = self.review('Ég egy pacsai épület.', '')
        self.assertEqual({m.settlement_name for m in result.mentions}, {'Pacsa'})
        self.assertTrue(all(not m.context_hints for m in result.mentions))
