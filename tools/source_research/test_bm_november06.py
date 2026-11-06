"""Gyál locative, road direction and responder separation regressions."""
import unittest
from bm_hu_gazetteer import load_review_places
from bm_location_candidates import review_locations
from bm_fire_scope import review_fire_scope


class November06Tests(unittest.TestCase):
    def test_gyal_nearby_and_direction(self):
        title = "Árokba sodródott egy autó az M5-ösön, Gyálnál"
        description = ("Megpördült és árokba csapódott egy személyautó az M5-ös autópálya "
                       "Szeged felé vezető oldalán, Gyál közelében, a 27-es és 28-as kilométerszelvénynél. "
                       "A balesethez a fővárosi hivatásos tűzoltókat riasztották, akik áramtalanították a járművet. "
                       "A helyszínre mentő is érkezett.")
        result = review_locations(title, description, "", load_review_places())
        self.assertEqual([m.settlement_name for m in result.mentions if m.field == "title"], ["Gyál"])
        self.assertEqual({m.settlement_name for m in result.mentions}, {"Gyál", "Szeged"})
        direction = [m for m in result.mentions if m.settlement_name == "Szeged"]
        self.assertTrue(all(any(h.kind == "direction_reference" for h in m.context_hints) for m in direction))
        self.assertFalse(result.incident_location_verified)
        self.assertEqual(review_fire_scope(title, description)["category"], "non_fire_report_candidate")

    def test_named_responder_is_not_incident_place(self):
        result = review_locations("Baleset Gyálnál", "Szeged felé haladtak. A répcelaki hivatásos tűzoltók vonultak ki.", "", load_review_places())
        self.assertEqual({m.settlement_name for m in result.mentions}, {"Gyál", "Szeged", "Répcelak"})
        for town, hint in (("Szeged", "direction_reference"), ("Répcelak", "responder_reference")):
            mentions = [m for m in result.mentions if m.settlement_name == town]
            self.assertTrue(mentions)
            self.assertTrue(all(any(h.kind == hint for h in m.context_hints) for m in mentions))
        self.assertFalse(result.incident_location_verified)

    def test_tuzser_and_shared_brigade_list(self):
        result = review_locations("Kigyulladt egy ház egyik szobája Tuzséron",
            "Tűz keletkezett Tuzséron. A kisvárdai és a záhonyi hivatásos tűzoltók eloltották.", "", load_review_places())
        self.assertEqual({m.settlement_name for m in result.mentions}, {"Tuzsér", "Kisvárda", "Záhony"})
        for mention in result.mentions:
            kinds = {h.kind for h in mention.context_hints}
            if mention.settlement_name in {"Kisvárda", "Záhony"}:
                self.assertIn("responder_list_reference", kinds)
            else:
                self.assertFalse(kinds)
        self.assertFalse(result.incident_location_verified)

    def test_siofok_incident_and_responder(self):
        result = review_locations("Autók ütköztek Siófokon",
            "A siófoki hivatásos tűzoltók áramtalanítottak.", "", load_review_places())
        self.assertEqual(len(result.mentions), 2)
        for mention in result.mentions:
            self.assertEqual(mention.settlement_name, "Siófok")
            self.assertEqual(bool(mention.context_hints), mention.field == "description")
        self.assertFalse(result.incident_location_verified)

    def test_traffic_obstruction_does_not_obscure_accident(self):
        result = review_fire_scope("Három autó karambolozott Zuglóban",
            "Az érintett útszakaszon forgalmi akadályra lehet számítani.")
        self.assertEqual(result["category"], "non_fire_report_candidate")
        self.assertFalse(result["automatically_excluded"])

    def test_real_uncertainty_survives_traffic_phrase(self):
        for extra in ("Lehet, hogy tűz van.", "Feltételezett baleset.", "Ez gyakorlat."):
            with self.subTest(extra=extra):
                result = review_fire_scope("Három autó karambolozott",
                    "Forgalmi akadályra lehet számítani. " + extra)
                self.assertEqual(result["category"], "unknown")
                self.assertTrue(any(e["kind"] == "uncertain" for e in result["evidence"]))

    def test_separate_place_sentence_not_brigade_list(self):
        result = review_locations("Tűz Tuzséron",
            "Kisvárda érintett. A záhonyi hivatásos tűzoltók kivonultak.", "", load_review_places())
        kisvarda = [m for m in result.mentions if m.settlement_name == "Kisvárda"]
        self.assertTrue(kisvarda)
        self.assertFalse(kisvarda[0].context_hints)
