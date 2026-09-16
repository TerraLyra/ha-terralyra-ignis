import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from nifc_refresh import RefreshState
from nifc_storage import FILENAME, load_cooldown, save_cooldown


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name)
        self.path = self.directory / FILENAME

    def test_roundtrip_contains_only_policy_metadata(self):
        save_cooldown(self.directory, RefreshState(next_attempt_at=200,failures=2), now=100)
        self.assertEqual(json.loads(self.path.read_text()),
                         {'version':1,'wait_seconds':100,'failures':2})
        self.assertEqual(load_cooldown(self.directory,now=10).next_attempt_at,110)

    def test_separate_process_restores_wait(self):
        save_cooldown(self.directory,RefreshState(next_attempt_at=200),now=100)
        environment = dict(os.environ, PYTHONPATH=str(Path(__file__).parent.resolve()))
        code = ('import sys; from nifc_storage import load_cooldown; '
                'print(load_cooldown(sys.argv[1],now=5).next_attempt_at)')
        completed = subprocess.run([sys.executable,'-c',code,str(self.directory)],
                                   env=environment,check=True,capture_output=True,text=True,timeout=10)
        self.assertEqual(completed.stdout.strip(),'105')

    def test_failed_replace_preserves_old_file_and_unrelated_history(self):
        save_cooldown(self.directory,RefreshState(next_attempt_at=100),now=0)
        original=self.path.read_bytes()
        history=self.directory/'history.json'; history.write_bytes(b'untouched history')
        with patch('nifc_storage.os.replace',side_effect=OSError('synthetic disk failure')):
            with self.assertRaises(OSError):
                save_cooldown(self.directory,RefreshState(next_attempt_at=500),now=0)
        self.assertEqual(self.path.read_bytes(),original)
        self.assertEqual(history.read_bytes(),b'untouched history')
        self.assertEqual(sorted(p.name for p in self.directory.iterdir()),['history.json',FILENAME])

    def test_missing_corrupt_duplicate_and_large_files_never_reset(self):
        with self.assertRaises(FileNotFoundError): load_cooldown(self.directory,now=0)
        for payload in (b'{', b'{}', b'x'*4097,
                        b'{"version":1,"version":1,"wait_seconds":0,"failures":0}'):
            self.path.write_bytes(payload)
            with self.assertRaises(ValueError): load_cooldown(self.directory,now=0)
            self.assertEqual(self.path.read_bytes(),payload)

    def test_manual_pause_roundtrips_as_json_null(self):
        save_cooldown(self.directory,RefreshState(next_attempt_at=math.inf),now=0)
        self.assertIsNone(json.loads(self.path.read_text())['wait_seconds'])
        self.assertEqual(load_cooldown(self.directory,now=0).next_attempt_at,math.inf)

    def test_symlink_target_is_not_modified(self):
        target=self.directory/'history.json'; target.write_text('preserve')
        self.path.symlink_to(target)
        with self.assertRaises(ValueError): save_cooldown(self.directory,RefreshState(),now=0)
        with self.assertRaises(ValueError): load_cooldown(self.directory,now=0)
        self.assertEqual(target.read_text(),'preserve')
