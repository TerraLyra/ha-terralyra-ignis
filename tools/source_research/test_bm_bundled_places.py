"""Research adapter checks with the packaged database and synthetic notices."""
import hashlib
from pathlib import Path
import sqlite3
import tempfile
import unittest
from bm_bundled_places import DATABASE, load_hungarian_places
from bm_location_candidates import review_locations


class BundledTests(unittest.TestCase):
    def test_packaged_database_unchanged_and_no_coordinates_exposed(self):
        before = hashlib.sha256(DATABASE.read_bytes()).hexdigest()
        places = load_hungarian_places()
        self.assertGreater(len(places), 1000)
        self.assertEqual(len(places), len({p.identifier for p in places}))
        self.assertFalse(hasattr(places[0], 'latitude'))
        self.assertEqual(before, hashlib.sha256(DATABASE.read_bytes()).hexdigest())

    def test_inflected_event_and_responder_mentions_still_need_review(self):
        result = review_locations('Tűz egy vértesszőlősi házban',
            'Tatabányai tűzoltók érkeztek.', '', load_hungarian_places())
        self.assertEqual({m.settlement_name for m in result.mentions}, {'Vértesszőlős', 'Tatabánya'})
        self.assertTrue(result.multiple_candidates)
        self.assertFalse(result.incident_location_verified)

    def test_unlisted_alias_is_not_guessed(self):
        result = review_locations('Szegedről', '', '', load_hungarian_places())
        self.assertEqual(result.mentions, ())

    def test_missing_file_is_not_created(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / 'missing.sqlite3'
            with self.assertRaises(sqlite3.OperationalError):
                load_hungarian_places(missing)
            self.assertFalse(missing.exists())

    def test_homonyms_remain_distinct_and_wrong_source_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'places.sqlite3'
            c = sqlite3.connect(path)
            c.executescript("CREATE TABLE metadata(key TEXT,value TEXT); INSERT INTO metadata VALUES('source','GeoNames cities500'); CREATE TABLE places(name TEXT,admin1_code TEXT,latitude REAL,longitude REAL,country_code TEXT);")
            c.executemany('INSERT INTO places VALUES(?,?,?,?,?)', [('Same','01',1,2,'HU'),('Same','02',3,4,'HU'),('Other','03',5,6,'AT')])
            c.commit()
            places = load_hungarian_places(path)
            self.assertEqual(len(places), 2)
            self.assertNotEqual(places[0].identifier, places[1].identifier)
            self.assertTrue(review_locations('Same', '', '', places).multiple_candidates)
            c.execute("UPDATE metadata SET value='Unexpected'")
            c.commit()
            with self.assertRaises(ValueError):
                load_hungarian_places(path)
            c.close()

class IndependentSampleRegressionTests(unittest.TestCase):
    def test_inflected_railway_location_retains_route_ambiguity(self):
        result = review_locations('Baleset Berettyóújfalun',
            'Püspökladányba tartott. Berettyóújfalu és Biharkeresztes között busz jár.',
            '', load_hungarian_places())
        self.assertEqual({m.settlement_name for m in result.mentions},
                         {'Berettyóújfalu', 'Biharkeresztes', 'Püspökladány'})
        self.assertTrue(result.multiple_candidates)
        self.assertFalse(result.incident_location_verified)

    def test_responders_do_not_fill_missing_event_location(self):
        result = review_locations('Tűz Gersekaráton',
            'Vasvári önkormányzati tűzoltók, körmendi és zalaegerszegi hivatásos tűzoltók érkeztek.',
            '', load_hungarian_places())
        self.assertEqual({m.settlement_name for m in result.mentions},
                         {'Vasvár', 'Körmend', 'Zalaegerszeg'})
        self.assertTrue(all(m.context_hints for m in result.mentions))
        self.assertFalse(result.incident_location_verified)


class OctoberPlaceTests(unittest.TestCase):
    def test_reviewed_small_settlements_and_responder_lists(self):
        from bm_hu_gazetteer import load_review_places
        places = load_review_places()
        for title, description, location, responders in [
            ('Tűz volt Sámsonházán', 'A pásztói hivatásos tűzoltók eloltották a lángokat.',
             'Sámsonháza', {'Pásztó'}),
            ('Családi ház égett Misefán', 'A pacsai, a zalaegerszegi és a keszthelyi hivatásos tűzoltók dolgoznak.',
             'Misefa', {'Pacsa', 'Zalaegerszeg', 'Keszthely'}),
        ]:
            with self.subTest(location=location):
                result = review_locations(title, description, '', places)
                self.assertIn(location, {m.settlement_name for m in result.mentions if m.field == 'title'})
                marked = {m.settlement_name for m in result.mentions
                          if any(h.kind in ('responder_reference', 'responder_list_reference')
                                 for h in m.context_hints)}
                self.assertEqual(marked, responders)
                self.assertFalse(result.incident_location_verified)


class KutasContextTests(unittest.TestCase):
    def test_kutas_event_area_quantity_and_responders(self):
        from bm_hu_gazetteer import load_review_places
        places = load_review_places()
        body = 'Egy hatvan négyzetméteres épület ég Kutason, a Szellő utcában. A nagyatádi hivatásos, a böhönyei önkormányzati és a nagybajomi önkéntes tűzoltók dolgoznak.'
        result = review_locations('Tűz Kutason', body, '', places)
        self.assertIn('Kutas', {m.settlement_name for m in result.mentions if m.field == 'title'})
        for name, hint in [('Hatvan', 'area_quantity_reference'), ('Szellő', 'street_name_reference'),
                           ('Nagyatád', 'responder_list_reference'), ('Böhönye', 'responder_list_reference'),
                           ('Nagybajom', 'responder_list_reference')]:
            self.assertTrue(any(m.settlement_name == name and any(h.kind == hint for h in m.context_hints) for m in result.mentions), name)
        self.assertFalse(result.incident_location_verified)
        genuine = review_locations('Hatvan', 'Hatvan közelében történt.', '', places)
        self.assertTrue(genuine.mentions)
        self.assertFalse(any(h.kind == 'area_quantity_reference' for m in genuine.mentions for h in m.context_hints))
        for m in result.mentions:
            for h in m.context_hints:
                self.assertEqual(getattr(result, m.field)[h.start:h.end], h.evidence)
