"""BM OKF RSS 92474/92473: accident locations remain unverified candidates."""
import unittest

from bm_bundled_places import load_hungarian_places
from bm_hu_gazetteer import load_review_places
from bm_location_candidates import review_locations
from bm_fire_scope import review_fire_scope


class October2Review(unittest.TestCase):
    def test_observed_title_form_in_both_bundled_databases(self):
        title = 'Felborult egy betonszállító Gyöngyöshalásznál'
        for loader in (load_hungarian_places, load_review_places):
            with self.subTest(loader=loader.__name__):
                result = review_locations(title, '', '', loader())
                self.assertEqual({m.settlement_name for m in result.mentions}, {'Gyöngyöshalász'})
                for mention in result.mentions:
                    self.assertEqual(mention.evidence, 'Gyöngyöshalásznál')
                    self.assertEqual(title[mention.start:mention.end], mention.evidence)
                    self.assertEqual(mention.context_hints, ())
                self.assertEqual(result.title, title)
                self.assertFalse(result.incident_location_verified)

    def test_alias_does_not_match_inside_longer_words(self):
        result = review_locations('XGyöngyöshalásznál GyöngyöshalásználX', '', '', load_review_places())
        self.assertEqual(result.mentions, ())

    def test_accident_samples_are_not_fire_reports(self):
        samples = (
            ('Felborult egy betonszállító Gyöngyöshalásznál',
             'Felborult egy betonszállító teherautó Gyöngyöshalász határában, a Móczár tanya közelében.'),
            ('Karambol az M5-ösön',
             'Összeütközött egy kamion és egy kistehergépkocsi az M5-ös autópálya Budapest felé vezető oldalán, Lajosmizse térdégében, a 62. kilométernél.'),
        )
        for title, description in samples:
            with self.subTest(title=title):
                scope = review_fire_scope(title, description)
                self.assertEqual(scope['category'], 'non_fire_report_candidate')
                self.assertFalse(scope['large_extent_verified'])

    def test_motorway_direction_is_not_the_incident_town(self):
        # Retain the upstream spelling; do not silently correct the source text.
        description = 'Az M5-ös autópálya Budapest felé vezető oldalán, Lajosmizse térdégében.'
        result = review_locations('Karambol az M5-ösön', description, '', load_review_places())
        self.assertEqual(result.description, description)
        self.assertEqual({m.settlement_name for m in result.mentions}, {'Budapest', 'Lajosmizse'})
        for mention in result.mentions:
            if mention.settlement_name == 'Budapest':
                self.assertIn('direction_reference', {h.kind for h in mention.context_hints})
            else:
                self.assertEqual(mention.context_hints, ())
        self.assertFalse(result.incident_location_verified)
