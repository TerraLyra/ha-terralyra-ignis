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
