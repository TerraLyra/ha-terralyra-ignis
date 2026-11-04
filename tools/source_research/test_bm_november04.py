"""Traffic permission must not obscure accident classification."""
import unittest
from bm_hu_gazetteer import load_review_places
from bm_location_candidates import review_locations
from bm_fire_scope import review_fire_scope


class November04Tests(unittest.TestCase):
    def test_traffic_permission_and_real_uncertainty(self):
        for body, category in (
            ('A főúton csak félpályán lehet közlekedni.', 'non_fire_report_candidate'),
            ('A főúton LEHET KÖZLEKEDNI.', 'non_fire_report_candidate'),
            ('Lehet közlekedni, de lehet, hogy tűz is van.', 'unknown'),
            ('Lehet, hogy baleset történt. Félpályán lehet közlekedni.', 'unknown'),
            ('Nem lehet közlekedni.', 'unknown'),
            ('Gyakorlat zajlik. Félpályán lehet közlekedni.', 'unknown'),
            ('Az autó füstöl. Félpályán lehet közlekedni.', 'unknown'),
        ):
            with self.subTest(body=body):
                result = review_fire_scope('Karambol történt', body)
                self.assertEqual(result['category'], category)
                self.assertFalse(result['automatically_excluded'])
        result = review_fire_scope('Karambol történt', 'Lehet közlekedni, de lehet tűz is.')
        self.assertEqual([e['evidence'] for e in result['evidence'] if e['kind'] == 'uncertain'], ['lehet'])
        self.assertEqual(review_fire_scope('Karambol történt', 'Lehet közlekedni.', input_truncated=True)['category'], 'unknown')

    def test_responder_town_is_not_event_town(self):
        places = load_review_places()
        for town in ('Kőszeg', 'Tárnok'):
            result = review_locations(f'Karambol történt {town} határában',
                'A kőszegi önkormányzati tűzoltók végzik a műszaki mentést.', '', places)
            self.assertEqual({m.settlement_name for m in result.mentions if not m.context_hints}, {town})
            units = [m for m in result.mentions if m.field == 'description']
            self.assertEqual([m.settlement_name for m in units], ['Kőszeg'])
            self.assertTrue(all(any(h.kind == 'responder_reference' for h in m.context_hints) for m in units))
            self.assertFalse(result.incident_location_verified)
        result = review_locations('', 'A kőszegi és az érdi hivatásos tűzoltók vonultak ki.', '', places)
        self.assertEqual({m.settlement_name for m in result.mentions}, {'Kőszeg', 'Érd'})
        self.assertTrue(all(any(h.kind == 'responder_list_reference' for h in m.context_hints) for m in result.mentions))
