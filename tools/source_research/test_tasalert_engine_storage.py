import json
from dataclasses import replace
from datetime import datetime, UTC, timedelta
from pathlib import Path
import tempfile
import unittest
from tasalert_engine import Engine, advance
from tasalert_engine_storage import encode,decode,save,load
from test_tasalert_snapshot import record


class EngineStorageTests(unittest.TestCase):
    def setUp(self):
        self.now=datetime(2026,10,12,tzinfo=UTC)
        base=advance(Engine(),self.now,200,record(),etag='"a"')
        self.engine=advance(base,self.now+timedelta(hours=1),200,record(number='conflict'),etag='"b"')

    def test_conflict_and_validator_survive_restart_together(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'state'
            save(path,self.engine)
            restored=load(path)
        self.assertEqual(restored,self.engine)
        self.assertEqual(restored.ledger['one']['record']['fields']['number'],'A')
        self.assertEqual(restored.response.etag,'"b"')
        cached=advance(restored,self.now+timedelta(hours=2),304)
        self.assertEqual(cached.review,('one',))

    def test_corrupt_ledger_rejected(self):
        for mutate in (
            lambda d:d['ledger']['one']['record']['point'].update(latitude=999),
            lambda d:d['ledger']['one'].update(last_seen='2026-10-12T00:00:00'),
            lambda d:d.update(review=[]),
            lambda d:d['ledger']['one']['record'].update(id='other'),
        ):
            data=json.loads(encode(self.engine));mutate(data)
            with self.assertRaises(ValueError):decode(json.dumps(data).encode())

    def test_expiry_action_not_replayed(self):
        self.assertEqual(decode(encode(replace(self.engine,expired=('old',)))).expired,())
