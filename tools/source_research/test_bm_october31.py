"""Offline appliance fire and incident/responder adjective regressions."""
import unittest
from bm_hu_gazetteer import load_review_places
from bm_location_candidates import review_locations
from bm_fire_scope import review_fire_scope


class October31Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.places = load_review_places()

    def test_event_and_responder_same_adjective(self):
        result = review_locations(
            'Tűz volt egy békéscsabai lakóházban',
            'A békéscsabai hivatásos tűzoltók eloltották a lángokat.', '', self.places)
        event = [m for m in result.mentions if m.field == 'title']
        units = [m for m in result.mentions if m.field == 'description']
        self.assertEqual([m.settlement_name for m in event], ['Békéscsaba'])
        self.assertFalse(event[0].context_hints)
        self.assertEqual([m.settlement_name for m in units], ['Békéscsaba'])
        self.assertIn('responder_reference', [h.kind for h in units[0].context_hints])
        self.assertFalse(result.incident_location_verified)

    def test_responder_list_and_different_event_town(self):
        result = review_locations('Tűz volt Pakson',
            'A békéscsabai és a gödöllői hivatásos tűzoltók vonultak ki.', '', self.places)
        self.assertEqual([m.settlement_name for m in result.mentions if m.field == 'title'], ['Paks'])
        units = [m for m in result.mentions if m.field == 'description']
        self.assertEqual({m.settlement_name for m in units}, {'Békéscsaba', 'Gödöllő'})
        self.assertTrue(all(any(h.kind == 'responder_list_reference' for h in m.context_hints) for m in units))
        self.assertFalse(result.incident_location_verified)

    def test_appliance_fire_and_non_fire_controls(self):
        for text, expected in (
            ('A helyiségben egy mosógép égett. A lángokat eloltották.', 'local_asset_fire_candidate'),
            ('Mosógéptűz volt a fürdőszobában.', 'local_asset_fire_candidate'),
            ('A mosógépet szállították.', 'unknown'),
            ('A mosógép nem égett.', 'unknown'),
            ('Gyakorlat: mosógéptűz.', 'unknown'),
            ('Mosógépszerelő érkezett. Tűz volt az utcában.', 'unknown'),
        ):
            with self.subTest(text=text):
                result = review_fire_scope('', text)
                self.assertEqual(result['category'], expected)
                self.assertTrue(result['requires_review'])
                self.assertFalse(result['automatically_excluded'])
        self.assertEqual(review_fire_scope('', 'Mosógéptűz.', input_truncated=True)['category'], 'unknown')
