"""Road-accident review and responder/location separation regressions."""
import unittest
from bm_hu_gazetteer import load_review_places
from bm_location_candidates import review_locations
from bm_fire_scope import review_fire_scope


class November01Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.places = load_review_places()

    def test_locations_and_responding_units(self):
        for title, body, town, responder in (
            ('Baleset történt Tárnokon',
             'Két gépkocsi ütközött Tárnokon. Az érdi hivatásos tűzoltók áramtalanították a járműveket.',
             'Tárnok', 'Érd'),
            ('Árokba hajtott egy autó',
             'Árokba hajtott egy gépkocsi Hortobágy térségében. A balmazújvárosi önkormányzati tűzoltók áramtalanították.',
             'Hortobágy', 'Balmazújváros'),
        ):
            with self.subTest(town=town):
                result = review_locations(title, body, '', self.places)
                event = [m for m in result.mentions if not m.context_hints]
                units = [m for m in result.mentions if any(h.kind == 'responder_reference' for h in m.context_hints)]
                self.assertEqual({m.settlement_name for m in event}, {town})
                self.assertEqual({m.settlement_name for m in units}, {responder})
                self.assertFalse(result.incident_location_verified)
                self.assertEqual(review_fire_scope(title, body)['category'], 'non_fire_report_candidate')

    def test_responder_only_list(self):
        result = review_locations('', 'Az érdi és a balmazújvárosi hivatásos tűzoltók vonultak ki.', '', self.places)
        self.assertEqual({m.settlement_name for m in result.mentions}, {'Érd', 'Balmazújváros'})
        self.assertTrue(all(any(h.kind == 'responder_list_reference' for h in m.context_hints) for m in result.mentions))
        self.assertFalse(result.incident_location_verified)

    def test_accident_clues_keep_fire_and_uncertainty_guards(self):
        for text, expected in (
            ('Árokba hajtott egy autó.', 'non_fire_report_candidate'),
            ('A balesethez mentő érkezett.', 'non_fire_report_candidate'),
            ('Árokba hajtott egy autó. Füst szállt fel.', 'unknown'),
            ('Árokba hajtott egy autó, amely kigyulladt.', 'local_asset_fire_candidate'),
            ('Nem hajtott árokba. Balesethez sem vonultak.', 'unknown'),
            ('Gyakorlat: árokba hajtott egy autó.', 'unknown'),
            ('Balesethez mentek.', 'non_fire_report_candidate'),
            ('Balesethezkapcsolódó feladat.', 'unknown'),
        ):
            with self.subTest(text=text):
                result = review_fire_scope('', text)
                self.assertEqual(result['category'], expected)
                self.assertFalse(result['automatically_excluded'])
        self.assertEqual(review_fire_scope('', 'Árokba hajtott egy autó.', input_truncated=True)['category'], 'unknown')
