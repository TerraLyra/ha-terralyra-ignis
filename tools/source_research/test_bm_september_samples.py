"""Regressions from BM OKF RSS 92320 and 92341, no linked-page retrieval."""
import unittest
from bm_hu_gazetteer import load_review_places
from bm_location_candidates import review_locations
from bm_fire_scope import review_fire_scope


class SeptemberSamples(unittest.TestCase):
    def test_inflected_places_and_street_context(self):
        places = load_review_places()
        for title, description, expected, street in (
            ('Baleset történt Dunaújvárosban', 'Dunaújvárosban, a Hajós utca mellett.', 'Dunaújváros', 'Hajós'),
            ('Tűz volt Pálfán', 'Személyautó égett Pálfán, a Teleki utcában.', 'Pálfa', 'Teleki'),
        ):
            result = review_locations(title, description, '', places)
            self.assertTrue(any(m.settlement_name == expected for m in result.mentions))
            street_mentions = [m for m in result.mentions if m.settlement_name == street]
            self.assertTrue(street_mentions)
            self.assertTrue(all(any(c.kind == 'street_name_reference' for c in m.context_hints) for m in street_mentions))
            self.assertFalse(result.incident_location_verified)

    def test_firefighter_possessive_is_not_fire(self):
        result = review_fire_scope('Baleset történt Dunaújvárosban',
                                  'Két gépkocsi ütközött. A város tűzoltóinak kiérkezése előtt kiszálltak.')
        self.assertEqual(result['category'], 'non_fire_report_candidate')
        self.assertFalse(result['automatically_excluded'])

    def test_fire_is_retained_with_firefighters(self):
        result = review_fire_scope('Baleset történt', 'A tűzoltóinak kiérkezése előtt kigyulladt egy autó.')
        self.assertEqual(result['category'], 'local_asset_fire_candidate')
        self.assertFalse(result['automatically_excluded'])
