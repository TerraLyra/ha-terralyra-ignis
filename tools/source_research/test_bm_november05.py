"""Review regression for extinguished fires and responding brigades."""
import unittest
from bm_hu_gazetteer import load_review_places
from bm_location_candidates import review_locations
from bm_fire_scope import review_fire_scope


class November05Tests(unittest.TestCase):
    def test_places_and_responder(self):
        places = load_review_places()
        for form, town in (('Miskolcon', 'Miskolc'), ('Ivánon', 'Iván')):
            result = review_locations('Tűz volt ' + form,
                'A répcelaki önkormányzati tűzoltók eloltották a lángokat.', '', places)
            self.assertEqual([m.settlement_name for m in result.mentions if m.field == 'title'], [town])
            units = [m for m in result.mentions if m.field == 'description']
            self.assertEqual([m.settlement_name for m in units], ['Répcelak'])
            self.assertTrue(all(any(h.kind == 'responder_reference' for h in m.context_hints) for m in units))
            self.assertFalse(result.incident_location_verified)
        result = review_locations('', 'A répcelaki és az érdi hivatásos tűzoltók vonultak ki.', '', places)
        self.assertEqual({m.settlement_name for m in result.mentions}, {'Répcelak', 'Érd'})
        self.assertTrue(all(any(h.kind == 'responder_list_reference' for h in m.context_hints) for m in result.mentions))

    def test_spread_denial_and_real_negation(self):
        for text, expected in (
            ('Elhagyatott ikerház tetőszerkezete égett. A tűz nem terjedt tovább. Eloltották a lángokat.', 'local_asset_fire_candidate'),
            ('Nem égett az ikerház. A tűz nem terjedt tovább.', 'unknown'),
            ('Ikerház égett. Lehet, hogy a tűz nem terjedt tovább.', 'unknown'),
            ('Gyakorlat: ikerház égett. A tűz nem terjedt tovább.', 'unknown'),
            ('Az ikerház mellett jártak.', 'unknown'),
            ('A tűz nem terjedt tovább.', 'unknown'),
        ):
            with self.subTest(text=text):
                result = review_fire_scope('', text)
                self.assertEqual(result['category'], expected)
                self.assertTrue(result['requires_review'])
                self.assertFalse(result['automatically_excluded'])
        self.assertEqual(review_fire_scope('', 'Ikerház égett. A tűz nem terjedt tovább.', input_truncated=True)['category'], 'unknown')
