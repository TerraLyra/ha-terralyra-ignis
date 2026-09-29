"""Independent RSS wording; preserve ambiguity rather than geolocate automatically."""
import unittest
from bm_hu_gazetteer import load_review_places
from bm_location_candidates import review_locations
from bm_fire_scope import review_fire_scope

class September29Review(unittest.TestCase):
    def test_mako_inflection_and_building(self):
        title = 'Kigyulladt egy melléképület Makón'
        result = review_locations(title, 'Tűz ütött ki egy melléképületben, Makón.', '', load_review_places())
        self.assertEqual({m.settlement_name for m in result.mentions}, {'Makó'})
        self.assertFalse(result.incident_location_verified)
        self.assertEqual(review_fire_scope(title, '')['category'], 'local_asset_fire_candidate')

    def test_direction_is_not_incident_location(self):
        result = review_locations('', 'Az M1-es autópálya Budapest felé vezető oldalán, Károlyháza térségében.', '', load_review_places())
        budapest = next(m for m in result.mentions if m.settlement_name == 'Budapest')
        self.assertIn('direction_reference', [h.kind for h in budapest.context_hints])
        self.assertFalse(result.incident_location_verified)
        result = review_locations('', 'Budapest XVIII. kerületében történt.', '', load_review_places())
        self.assertFalse(any(h.kind == 'direction_reference' for m in result.mentions for h in m.context_hints))

    def test_mixed_and_uncertain_are_retained(self):
        self.assertEqual(review_fire_scope('Ég a melléképület és a bozót.', '')['category'], 'mixed_fire_candidate')
        self.assertEqual(review_fire_scope('Nem ég a melléképület.', '')['category'], 'unknown')
        self.assertEqual(review_fire_scope('Kigyulladt egy melléképület.', '', input_truncated=True)['category'], 'unknown')
