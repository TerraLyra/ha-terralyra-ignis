import asyncio
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from nifc_fetch import FetchResult
from nifc_persistent import PersistentResearchCoordinator
from nifc_refresh import RefreshState, SourceHTTPError
from nifc_storage import FILENAME, load_cooldown, save_cooldown


class PersistentTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.directory=Path(self.tmp.name)
        save_cooldown(self.directory,RefreshState(),now=0)

    async def test_success_saved_and_restart_skips(self):
        calls=[]
        async def fetch():
            calls.append(1)
            self.assertEqual(load_cooldown(self.directory,now=0).next_attempt_at,math.inf)
            return FetchResult((),1,1,'terminal_reported')
        first=PersistentResearchCoordinator(self.directory,clock=lambda:10,fetcher=fetch)
        self.assertEqual(await first.refresh(enabled=True),'retrieved')
        second=PersistentResearchCoordinator(self.directory,clock=lambda:0,fetcher=fetch)
        self.assertEqual(await second.refresh(enabled=True),'skipped')
        self.assertEqual(len(calls),1)
        self.assertEqual(second.state.next_attempt_at,900)

    async def test_rate_limit_saved(self):
        async def fetch(): raise SourceHTTPError(429,'3600')
        coordinator=PersistentResearchCoordinator(self.directory,clock=lambda:0,fetcher=fetch)
        self.assertEqual(await coordinator.refresh(enabled=True),'failed')
        self.assertEqual(load_cooldown(self.directory,now=0).next_attempt_at,3600)

    async def test_failed_preflight_write_never_fetches(self):
        async def fetch(): self.fail('Network must not start')
        coordinator=PersistentResearchCoordinator(self.directory,fetcher=fetch)
        with patch('nifc_persistent.save_cooldown',side_effect=OSError('disk')):
            with self.assertRaises(OSError): await coordinator.refresh(enabled=True)
        self.assertEqual(await coordinator.refresh(enabled=True),'skipped')

    async def test_failed_final_write_keeps_pause_and_previous_snapshot(self):
        async def fetch(): return FetchResult((),1,1,'terminal_reported')
        coordinator=PersistentResearchCoordinator(self.directory,clock=lambda:0,fetcher=fetch)
        calls=[]
        def save(*args,**kwargs):
            calls.append(1)
            if len(calls)==2: raise OSError('disk')
            return save_cooldown(*args,**kwargs)
        with patch('nifc_persistent.save_cooldown',side_effect=save):
            with self.assertRaises(OSError): await coordinator.refresh(enabled=True)
        self.assertIsNone(coordinator.state.last_success)
        self.assertEqual(load_cooldown(self.directory,now=0).next_attempt_at,math.inf)

    async def test_cancellation_requires_review_after_restart(self):
        started=asyncio.Event()
        async def fetch(): started.set(); await asyncio.Future()
        coordinator=PersistentResearchCoordinator(self.directory,fetcher=fetch)
        task=asyncio.create_task(coordinator.refresh(enabled=True))
        await started.wait()
        self.assertEqual(await coordinator.refresh(enabled=True),'skipped')
        task.cancel()
        with self.assertRaises(asyncio.CancelledError): await task
        restarted=PersistentResearchCoordinator(self.directory,fetcher=fetch)
        self.assertEqual(await restarted.refresh(enabled=True),'skipped')

    async def test_disabled_does_not_write(self):
        coordinator=PersistentResearchCoordinator(self.directory)
        with patch('nifc_persistent.save_cooldown') as save:
            self.assertEqual(await coordinator.refresh(),'skipped')
            save.assert_not_called()

    async def test_missing_checkpoint_is_not_implicitly_initialized(self):
        (self.directory/FILENAME).unlink()
        with self.assertRaises(FileNotFoundError): PersistentResearchCoordinator(self.directory)
