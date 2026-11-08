"""RSS 93522: incident locality and responding brigades remain distinct."""
import unittest

from bm_hu_gazetteer import load_review_places
from bm_location_candidates import review_locations
from bm_fire_scope import review_fire_scope


class BacsborsodTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.places = load_review_places()

    def test_rss_incident_and_brigades(self):
        title = "Tűz ütött ki egy bácsborsódi házban"
        description = ("Kigyulladt egy földszintes családi ház Bácsborsódon, a Dózsa György utcában. "
                       "A helyszínre elsőként a bácsbokodi önkéntes tűzoltók érkeztek meg, "
                       "áramtalanították az épületet és megkezdték az oltást. "
                       "Az önkéntesekhez pár perccel ezután csatlakoztak a bajai hivatásos tűzoltók, "
                       "így már három vízsugárral oltják a lángokat.")
        result = review_locations(title, description, "", self.places)
        mentions = {(m.evidence.casefold(), m.field): m for m in result.mentions}
        for evidence, field in (("bácsborsódi", "title"), ("bácsborsódon", "description")):
            m = mentions[(evidence, field)]
            self.assertEqual(m.settlement_name, "Bácsborsód")
            self.assertFalse(any(h.kind.startswith("responder") for h in m.context_hints))
        for evidence, town in (("bácsbokodi", "Bácsbokod"), ("bajai", "Baja")):
            m = mentions[(evidence, "description")]
            self.assertEqual(m.settlement_name, town)
            self.assertIn("responder_reference", {h.kind for h in m.context_hints})
        self.assertFalse(result.incident_location_verified)
        self.assertEqual(review_fire_scope(title, description)["category"], "local_asset_fire_candidate")

    def test_adjectives_can_also_describe_incident_places(self):
        for adjective, town in (("bácsbokodi", "Bácsbokod"), ("bajai", "Baja"), ("bácsborsódi", "Bácsborsód")):
            with self.subTest(town=town):
                result = review_locations("Tűz egy " + adjective + " házban", "", "", self.places)
                mention = next(m for m in result.mentions if m.settlement_name == town)
                self.assertFalse(any(h.kind.startswith("responder") for h in mention.context_hints))
                self.assertFalse(result.incident_location_verified)
