"""BM RSS brigade lists remain distinct from incident place mentions."""
import unittest

from bm_hu_gazetteer import load_review_places
from bm_location_candidates import review_locations
from bm_fire_scope import review_fire_scope


class November08Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.places = load_review_places()

    def test_kenderes_fire_and_brigades(self):
        title = "Melléképület égett Kenderesen"
        description = ("Teljes terjedelmében égett egy melléképület Kenderesen, a Damjanich úton. "
                       "A tűz átterjedt a főépület tetőszerkezetére is. A karcagi hivatásos és a "
                       "kisújszállási önkormányzati tűzoltók egy vízsugárral elfojtották a lángokat. "
                       "A rajok az utómunkálatokat végzik.")
        result = review_locations(title, description, "", self.places)
        self.assertEqual({m.settlement_name for m in result.mentions}, {"Kenderes", "Karcag", "Kisújszállás"})
        for m in result.mentions:
            hints = {h.kind for h in m.context_hints}
            if m.settlement_name == "Kenderes":
                self.assertNotIn("responder_list_reference", hints)
            else:
                self.assertIn("responder_list_reference", hints)
        self.assertFalse(result.incident_location_verified)
        self.assertEqual(review_fire_scope(title, description)["category"], "local_asset_fire_candidate")

    def test_apatfalva_and_brigade_list_without_article(self):
        title = "Karambol az M43-on"
        description = ("Összeütközött egy kisbusz és egy furgon az M43-as autópályán, "
                       "a határ felé vezető oldalon, Apátfalva közelében, a 48-as kilométerszelvénynél. "
                       "A makói és hódmezővásárhelyi hivatásos tűzoltók áramtalanították a járműveket "
                       "és három utast feszítővágó segítségével kimentettek. "
                       "Az érintett útszakaszt teljes szélességében lezárták.")
        result = review_locations(title, description, "", self.places)
        self.assertEqual({m.settlement_name for m in result.mentions}, {"Apátfalva", "Makó", "Hódmezővásárhely"})
        for m in result.mentions:
            hints = {h.kind for h in m.context_hints}
            if m.settlement_name == "Apátfalva":
                self.assertNotIn("responder_list_reference", hints)
            else:
                self.assertIn("responder_list_reference", hints)
        self.assertFalse(result.incident_location_verified)
        self.assertEqual(review_fire_scope(title, description)["category"], "non_fire_report_candidate")

    def test_adjectives_not_globally_treated_as_brigades(self):
        for adjective, town in (("karcagi", "Karcag"), ("kisújszállási", "Kisújszállás"),
                                ("hódmezővásárhelyi", "Hódmezővásárhely")):
            with self.subTest(town=town):
                result = review_locations("Tűz egy " + adjective + " házban", "", "", self.places)
                mention = next(m for m in result.mentions if m.settlement_name == town)
                self.assertFalse(any(h.kind.startswith("responder") for h in mention.context_hints))
                self.assertFalse(result.incident_location_verified)
