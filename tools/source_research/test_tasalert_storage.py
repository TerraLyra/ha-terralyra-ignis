import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from datetime import datetime, UTC, timedelta
from tasalert_policy import State, apply_response, request_headers
from tasalert_storage import save, load, encode, decode
from test_tasalert_snapshot import record


class StorageTests(unittest.TestCase):
    def setUp(self):
        now=datetime(2026,10,12,tzinfo=UTC)
        accepted=apply_response(State(),now,200,record(),etag='"a"')
        self.state=apply_response(accepted,now+timedelta(hours=1),429,retry_after='7200')

    def test_restart_preserves_payload_validator_and_backoff(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'state.json'
            save(path,self.state)
            restored=load(path)
            self.assertEqual(restored,self.state)
            self.assertEqual(request_headers(restored),{'If-None-Match':'"a"'})
            with self.assertRaises(ValueError):apply_response(restored,restored.next_attempt-timedelta(seconds=1),304)

    def test_failed_replace_keeps_prior_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'state.json'
            save(path,self.state)
            with patch('tasalert_storage.os.replace',side_effect=OSError('simulated')):
                with self.assertRaises(OSError):save(path,State())
            self.assertEqual(load(path),self.state)
            self.assertEqual(len(list(Path(directory).iterdir())),1)

    def test_corruption_is_not_silent_reset(self):
        original=json.loads(encode(self.state))
        for field,value in [('version',2),('snapshot','bad base64'),('next_attempt','2026-10-12T00:00:00'),('etag','bad\r\n'),('failures',-1)]:
            with self.subTest(field=field), self.assertRaises(ValueError):decode(json.dumps({**original,field:value}).encode())
        with self.assertRaises(ValueError):decode(b'{')
