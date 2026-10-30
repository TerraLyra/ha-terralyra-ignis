"""Locative mentions versus responding fire brigades, with bundled place data."""
import unittest
from bm_hu_gazetteer import load_review_places
from bm_location_candidates import review_locations
import test_bm_lightweight


class October30Tests(unittest.TestCase):
    def test_reviewed_inflections_and_responder_context(self):
        places = load_review_places()
        for town, adjective, locative, responder in (
            ('Paks', 'paksi', 'Pakson', 'paksi'),
            ('Erdőkertes', 'erdőkertesi', 'Erdőkertesen', 'gödöllői'),
        ):
            title = f'Tűz ütött ki egy {adjective} épületben'
            body = f'Kigyulladt egy melléképület {locative}. A {responder} hivatásos tűzoltók oltják a lángokat.'
            result = review_locations(title, body, '', places)
            event = [m for m in result.mentions if m.evidence == locative]
            self.assertEqual([m.settlement_name for m in event], [town])
            self.assertFalse(event[0].context_hints)
            units = [m for m in result.mentions if m.field == 'description' and m.evidence == responder]
            self.assertTrue(units)
            self.assertTrue(all(any(h.kind == 'responder_reference' for h in m.context_hints) for m in units))
            self.assertFalse(result.incident_location_verified)

    def test_runtime_retains_only_event_town(self):
        helper = test_bm_lightweight.LightweightTests()
        names = {'p': 'Paks', 'e': 'Erdőkertes', 'g': 'Gödöllő', 'k': 'Kalocsa'}
        for text, expected in (
            ('Kigyulladt egy ház tetőszerkezete Pakson, a Tolnai úton. A paksi hivatásos tűzoltók oltják. Egy gépjárműfecskendőt várnak Kalocsáról.', {'p'}),
            ('Kigyulladt egy melléképület Erdőkertesen, a Katona József utcában. A gödöllői hivatásos tűzoltók oltják a lángokat.', {'e'}),
            ('A paksi és erdőkertesi tűzoltók szerint ég egy ház.', set()),
            ('Pakson állomásozó tűzoltók szerint ég egy ház.', set()),
        ):
            report, _ = helper.run_text(text, names)
            self.assertEqual(report.event_settlement_ids, frozenset(expected), text)
