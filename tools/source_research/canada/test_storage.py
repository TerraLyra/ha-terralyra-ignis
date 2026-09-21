import json
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch
from retry import RefreshState
from storage import load, save

NOW=datetime(2026,9,21,tzinfo=UTC)
EMPTY={'type':'FeatureCollection','features':[],'numberMatched':0,'numberReturned':0}

class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'state.json'

    def test_restart_preserves_cooldown_and_data(self):
        state=RefreshState();state.refresh(lambda:(EMPTY,{}),NOW);save(self.path,state)
        restored=load(self.path);fetch=Mock()
        restored.refresh(fetch,NOW+timedelta(minutes=5))
        fetch.assert_not_called()
        self.assertEqual(restored.last_success[0],EMPTY)
        self.assertEqual(restored.last_success_at,NOW)

    def test_restart_preserves_review_hold(self):
        state=RefreshState(review_required=True,status='review_required',next_attempt=NOW)
        save(self.path,state);restored=load(self.path);fetch=Mock()
        restored.refresh(fetch,NOW+timedelta(days=3));fetch.assert_not_called()

    def test_corrupt_file_is_retained_and_blocks_fetch(self):
        self.path.write_text('broken')
        state=load(self.path);fetch=Mock();state.refresh(fetch,NOW)
        fetch.assert_not_called()
        with self.assertRaises(ValueError):save(self.path,state)
        self.assertEqual(self.path.read_text(),'broken')

    def test_failed_replace_preserves_previous_file(self):
        save(self.path,RefreshState());before=self.path.read_bytes()
        with patch('storage.os.replace',side_effect=OSError('disk')),self.assertRaises(OSError):
            save(self.path,RefreshState(failures=2))
        self.assertEqual(self.path.read_bytes(),before)

    def test_invalid_persisted_clock_blocks(self):
        save(self.path,RefreshState());data=json.loads(self.path.read_text())
        data['state']['next_attempt']='2026-09-21T00:00:00'
        self.path.write_text(json.dumps(data))
        self.assertTrue(load(self.path).review_required)

    def test_interrupted_request_keeps_reservation(self):
        from storage import refresh_persisted
        with self.assertRaises(KeyboardInterrupt):
            refresh_persisted(self.path,Mock(side_effect=KeyboardInterrupt()),NOW)
        fetch=Mock()
        refresh_persisted(self.path,fetch,NOW+timedelta(minutes=1))
        fetch.assert_not_called()

    def test_failed_reservation_prevents_network(self):
        from storage import refresh_persisted
        fetch=Mock()
        with patch('storage.save',side_effect=OSError('disk')),self.assertRaises(OSError):
            refresh_persisted(self.path,fetch,NOW)
        fetch.assert_not_called()
