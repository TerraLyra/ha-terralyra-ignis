import unittest
import tempfile
import sqlite3
from pathlib import Path
from copy import deepcopy
from test_bm_satellite_context import BMTownReport
from _bm_context_test.bm_context_lookup import lookup_context

class LookupTests(unittest.TestCase):
    def test_whole_local_pipeline_preserves_history_and_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'places.db'
            with sqlite3.connect(path) as db:
                db.executescript("CREATE TABLE metadata(key,value); INSERT INTO metadata VALUES ('source','GeoNames HU'),('schema_version','1'); CREATE TABLE hu_names(geoname_id,name,latitude,longitude); INSERT INTO hu_names VALUES (1,'Hejőbába',47.9,20.9);")
            class Resolver:
                def _resolve_sync(self,lat,lon):return ('Hejőbába','HU',2.,47.9,20.9)
            history=[dict(track_id='a',latitude=47.91,longitude=20.91,first_seen='2026-10-07T12:00:00+00:00',last_seen='2026-10-07T13:00:00+00:00')]
            notices=[dict(url='https://www.katasztrofavedelem.hu/modules/vesz/esemeny/1',published_at='2026-10-07T14:00:00+00:00',title='Hejőbábán égett egy ház',description='Eredeti leírás')]
            original=deepcopy((history,notices))
            result=lookup_context('a',history,notices,Resolver(),path)
            self.assertEqual(result['reports'][0]['relation'],'probable')
            self.assertEqual(result['reports'][0]['description'],'Eredeti leírás')
            self.assertEqual((history,notices),original)
            self.assertFalse(result['creates_incident'])
            with self.assertRaises(ValueError):lookup_context('missing',history,notices,Resolver(),path)
            with sqlite3.connect(path) as db:db.execute("INSERT INTO hu_names VALUES (2,'Hejőbába',48.,21.)")
            self.assertEqual(lookup_context('a',history,notices,Resolver(),path)['reports'],[])
