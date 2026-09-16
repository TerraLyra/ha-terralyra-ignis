"""Synthetic classifications; no real patient or incident records."""
import unittest
from act_feed import ActItem
from act_classification import classify_item, IncidentCategory as C, ExerciseEvidence as E


class ClassificationTests(unittest.TestCase):
    def test_official_test_label_remains_marked_candidate(self):
        item = ActItem((('type', 'GRASS AND BUSH FIRE'), ('title', 'TEST ONLY - HALL')))
        result = classify_item(item)
        self.assertEqual(result.category, C.VEGETATION_FIRE_CANDIDATE)
        self.assertEqual(result.exercise_evidence, E.MARKED)
        self.assertEqual(result.marker_fields, ('title',))
        self.assertEqual(item.fields[1][1], 'TEST ONLY - HALL')

    def test_no_marker_never_means_confirmed_real(self):
        result = classify_item(ActItem((('type', 'GRASS AND BUSH FIRE'),)))
        self.assertEqual(result.exercise_evidence, E.NOT_ESTABLISHED)
        self.assertEqual(result.marker_fields, ())

    def test_medical_is_not_fire_even_with_fire_words(self):
        result = classify_item(ActItem((('type', 'AMBULANCE RESPONSE'),
                                       ('title', 'Fire nearby'), ('agency', 'Fire'))))
        self.assertEqual(result.category, C.MEDICAL)

    def test_unknowns_not_guessed_from_title_or_agency(self):
        for value in ('', 'FIRE', 'STRUCTURE FIRE', 'BURN OFF', 'NEW TYPE'):
            with self.subTest(value=value):
                self.assertEqual(classify_item(ActItem((('type', value),
                    ('title', 'GRASS AND BUSH FIRE'), ('agency', 'Fire')))).category, C.UNKNOWN)

    def test_normalization_and_word_boundaries(self):
        result = classify_item(ActItem((('type', ' grass  and bush fire '),
                                       ('title', 'Latest report at Drilldown Road'))))
        self.assertEqual(result.category, C.VEGETATION_FIRE_CANDIDATE)
        self.assertEqual(result.exercise_evidence, E.NOT_ESTABLISHED)

    def test_marker_sources_are_explicit(self):
        for word in ('TEST', 'exercise', 'Drill'):
            with self.subTest(word=word):
                result = classify_item(ActItem((('description', word),)))
                self.assertEqual(result.exercise_evidence, E.MARKED)
                self.assertEqual(result.marker_fields, ('description',))

    def test_planned_burn_is_separate_from_fire_candidate(self):
        result = classify_item(ActItem((('type', 'HAZARD REDUCTION BURN'),
                                       ('title', 'Synthetic planned burn'))))
        self.assertEqual(result.category, C.PLANNED_BURN)
        self.assertEqual(result.exercise_evidence, E.NOT_ESTABLISHED)

    def test_test_marked_planned_burn_stays_marked(self):
        result = classify_item(ActItem((('type', 'HAZARD REDUCTION BURN'),
                                       ('title', 'TEST ONLY'))))
        self.assertEqual(result.category, C.PLANNED_BURN)
        self.assertEqual(result.exercise_evidence, E.MARKED)

    def test_planned_burn_words_do_not_override_source_type(self):
        result = classify_item(ActItem((('type', 'GRASS AND BUSH FIRE'),
                                       ('description', 'Near a hazard reduction burn'))))
        self.assertEqual(result.category, C.VEGETATION_FIRE_CANDIDATE)

    def test_house_fire_is_not_vegetation_fire(self):
        result = classify_item(ActItem((('type', 'HOUSE FIRE'),
                                       ('title', 'Near grass and bush fire'))))
        self.assertEqual(result.category, C.STRUCTURE_FIRE)
        self.assertEqual(result.exercise_evidence, E.NOT_ESTABLISHED)

    def test_test_house_fire_stays_marked(self):
        result = classify_item(ActItem((('type', ' house  fire '), ('title', 'TEST ONLY'))))
        self.assertEqual(result.category, C.STRUCTURE_FIRE)
        self.assertEqual(result.exercise_evidence, E.MARKED)

    def test_duplicate_fields_rejected(self):
        with self.assertRaises(ValueError):
            classify_item(ActItem((('type', 'AMBULANCE RESPONSE'), ('type', 'GRASS AND BUSH FIRE'))))


if __name__ == '__main__':
    unittest.main()
