"""Synthetic examples only; no live BM OKF content or gazetteer redistribution."""
import unittest
from bm_location_candidates import Settlement, review_locations

PLACES = (Settlement('egyek', 'Egyek', ('Egyeken',)),
          Settlement('szeged', 'Szeged', ('Szegeden',)))


class LocationTests(unittest.TestCase):
    def review(self, title='', description='', **kwargs):
        return review_locations(title, description, 'https://example.invalid/report', PLACES, **kwargs)

    def test_exact_original_evidence_and_offsets(self):
        result = self.review('Tűz EGYEKEN', 'Egyeken beavatkoztak.')
        self.assertEqual(result.status, 'requires_review')
        self.assertFalse(result.multiple_candidates)
        for m in result.mentions:
            self.assertEqual(getattr(result, m.field)[m.start:m.end], m.evidence)
        self.assertIn('EGYEKEN', [m.evidence for m in result.mentions])
        self.assertFalse(result.incident_location_verified)

    def test_unit_and_negated_mentions_never_become_verified_locations(self):
        result = self.review(description='Nem Egyeken történt. A szegedi egység Szegeden állomásozik.')
        self.assertTrue(result.multiple_candidates)
        self.assertFalse(result.incident_location_verified)
        self.assertEqual(result.status, 'requires_review')

    def test_substrings_and_unreviewed_inflections_do_not_match(self):
        self.assertEqual(self.review('Kisegyeken, egyeki, Szegedi').mentions, ())

    def test_shared_alias_keeps_ambiguity(self):
        result = review_locations('Közös', '', '',
            (Settlement('a', 'A', ('Közös',)), Settlement('b', 'B', ('Közös',))))
        self.assertEqual(len(result.mentions), 2)
        self.assertTrue(result.multiple_candidates)

    def test_truncated_input_is_preserved_without_inference(self):
        result = self.review(description='Egyeken', input_truncated=True)
        self.assertEqual(result.description, 'Egyeken')
        self.assertEqual(result.mentions, ())
        self.assertEqual(result.status, 'unknown')

    def test_bounds_and_duplicate_identifiers(self):
        with self.assertRaises(ValueError):
            self.review(description='x'*4001)
        with self.assertRaises(ValueError):
            review_locations('', '', '', (PLACES[0], PLACES[0]))

    def test_no_fire_classification_or_coordinate_fields(self):
        result = self.review('Közúti baleset Szegeden')
        self.assertEqual(result.status, 'requires_review')
        self.assertFalse(hasattr(result, 'latitude'))
        self.assertFalse(hasattr(result, 'is_fire'))


if __name__ == '__main__':
    unittest.main()
