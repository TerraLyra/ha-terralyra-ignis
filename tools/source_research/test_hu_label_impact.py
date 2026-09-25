import unittest
from hu_label_impact import compare, distance


class LabelImpactTests(unittest.TestCase):
    def test_identical_coordinates_and_known_equatorial_distance(self):
        self.assertEqual(distance((47, 19), (47, 19)), 0)
        self.assertAlmostEqual(distance((0, 0), (0, 1)), 111.195, places=3)

    def test_additive_data_does_not_remove_neighbour_country(self):
        result = compare((47, 16), [('Neighbour', 47, 16, 'cities500')], [('HU', 47, 17, 'PPL')])
        self.assertFalse(result['changed'])

    def test_ties_preserve_baseline(self):
        result = compare((47, 19), [('Known', 47, 19, 'cities500')], [('Other', 47, 19, 'PPLL')])
        self.assertEqual(result['after'], 'Known')

    def test_nearer_minor_place_is_explicit_change_not_accuracy_claim(self):
        result = compare((47, 19), [('Town', 47.1, 19, 'cities500')], [('Minor', 47, 19, 'PPLL')])
        self.assertTrue(result['changed'])
        self.assertEqual(result['selected_source'], 'PPLL')
        self.assertLess(result['after_km'], result['before_km'])
