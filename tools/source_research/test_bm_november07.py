"""BM 93488: distinguish event location, direction and responding brigade."""
import unittest

from bm_hu_gazetteer import load_review_places
from bm_location_candidates import review_locations
from bm_fire_scope import review_fire_scope


class November07Tests(unittest.TestCase):
    def test_ullo_location_monor_direction_and_brigade(self):
        title = "Szalagkorlátnak ütközött egy autó az M4-esen, Üllőnél"
        description = ("Szalagkorlátnak ütközött, majd megpördült egy gépkocsi az M4-es autóút "
                       "32-es és 33-as kilométerszelvénye között, Üllő térségében, a Monor felé vezető irányban. "
                       "A monori hivatásos tűzoltók és a társhatóságok érkeztek a helyszínre, az egység "
                       "áramtalanította a járművet, amelyben négyen utaztak. A hatósági beavatkozás idejére "
                       "lezárták az M4-es érintett szakaszát.")
        result = review_locations(title, description, "", load_review_places())
        mentions = {(m.evidence, m.field): m for m in result.mentions}
        self.assertEqual(mentions[("Üllőnél", "title")].settlement_name, "Üllő")
        self.assertEqual(mentions[("Üllő", "description")].settlement_name, "Üllő")
        self.assertEqual(mentions[("Monor", "description")].settlement_name, "Monor")
        self.assertEqual(mentions[("monori", "description")].settlement_name, "Monor")
        self.assertIn("direction_reference", {h.kind for h in mentions[("Monor", "description")].context_hints})
        self.assertIn("responder_reference", {h.kind for h in mentions[("monori", "description")].context_hints})
        self.assertFalse(mentions[("Üllőnél", "title")].context_hints)
        self.assertFalse(result.incident_location_verified)
        self.assertEqual(review_fire_scope(title, description)["category"], "non_fire_report_candidate")

    def test_monori_can_also_describe_incident_location(self):
        result = review_locations("Tűz egy monori házban", "", "", load_review_places())
        monor = [m for m in result.mentions if m.settlement_name == "Monor"]
        self.assertEqual(len(monor), 1)
        self.assertFalse(any(h.kind == "responder_reference" for h in monor[0].context_hints))
        self.assertFalse(result.incident_location_verified)
