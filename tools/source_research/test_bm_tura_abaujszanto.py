"""BM RSS 93533/93534: place, brigade and quantity contexts."""
import unittest
from bm_hu_gazetteer import load_review_places
from bm_location_candidates import review_locations
from bm_fire_scope import review_fire_scope


class TuraAbaujszantoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.places = load_review_places()

    def test_tura_and_hatvan_brigade(self):
        title = "Kigyulladt egy ház Turán"
        description = ("Egy nagyjából száz négyzetméteres családi ház tetőszerkezetének egy része, "
                       "illetve a közelében lévő melléképület gyulladt ki Turán. "
                       "A hatvani hivatásos tűzoltók vonultak az esethez.")
        result = review_locations(title, description, "", self.places)
        locations = [m for m in result.mentions if m.settlement_name == "Tura"]
        self.assertEqual(len(locations), 2)
        self.assertTrue(all(not any(h.kind.startswith("responder") for h in m.context_hints) for m in locations))
        brigade = next(m for m in result.mentions if m.settlement_name == "Hatvan")
        self.assertEqual(brigade.evidence, "hatvani")
        self.assertIn("responder_reference", {h.kind for h in brigade.context_hints})
        self.assertFalse(result.incident_location_verified)
        self.assertEqual(review_fire_scope(title, description)["category"], "local_asset_fire_candidate")

    def test_abaujszanto_encs_and_hatvan_quantity(self):
        title = "Tűz ütött ki egy abaújszántói melléképületben"
        description = ("Kigyulladt egy melléképület Abaújszántón, az Ady Endre utcában. "
                       "Egy családi ház hátsó udvarán áll a nagyjából hatvan négyzetméteres építmény. "
                       "Az encsi hivatásos tűzoltók három vízsugárral oltják a lángokat.")
        result = review_locations(title, description, "", self.places)
        places = [m for m in result.mentions if m.settlement_name == "Abaújszántó"]
        self.assertEqual({m.evidence for m in places}, {"abaújszántói", "Abaújszántón"})
        self.assertTrue(all(not any(h.kind.startswith("responder") for h in m.context_hints) for m in places))
        encs = next(m for m in result.mentions if m.settlement_name == "Encs")
        self.assertIn("responder_reference", {h.kind for h in encs.context_hints})
        hatvan = next(m for m in result.mentions if m.evidence == "hatvan")
        self.assertEqual(hatvan.settlement_name, "Hatvan")
        self.assertIn("area_quantity_reference", {h.kind for h in hatvan.context_hints})
        self.assertFalse(result.incident_location_verified)
        self.assertEqual(review_fire_scope(title, description)["category"], "local_asset_fire_candidate")

    def test_adjectives_can_be_incident_location(self):
        for adjective, town in (("hatvani", "Hatvan"), ("encsi", "Encs"), ("abaújszántói", "Abaújszántó")):
            with self.subTest(town=town):
                result = review_locations("Tűz egy " + adjective + " házban", "", "", self.places)
                m = next(m for m in result.mentions if m.settlement_name == town)
                self.assertFalse(any(h.kind.startswith("responder") for h in m.context_hints))
                self.assertFalse(result.incident_location_verified)
