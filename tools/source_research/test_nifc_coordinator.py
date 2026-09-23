import asyncio
from datetime import datetime, timezone
import math
import unittest

from nifc_coordinator import ResearchCoordinator, checkpoint, restore_checkpoint
from nifc_fetch import FetchResult
from nifc_refresh import RefreshState, SourceHTTPError


class CoordinatorTests(unittest.IsolatedAsyncioTestCase):
    async def test_disabled_then_success_then_cooldown(self):
        calls=[]
        async def fetch():
            calls.append(1); return FetchResult((),1,1,'terminal_reported')
        coordinator=ResearchCoordinator(fetcher=fetch,clock=lambda:100)
        self.assertEqual(await coordinator.refresh(),'skipped')
        self.assertEqual(await coordinator.refresh(enabled=True),'retrieved')
        self.assertEqual(await coordinator.refresh(enabled=True),'skipped')
        self.assertEqual(len(calls),1)

    async def test_concurrent_calls_do_not_queue_fetch(self):
        started, release=asyncio.Event(), asyncio.Event()
        async def fetch():
            started.set(); await release.wait()
            return FetchResult((),1,1,'terminal_reported')
        coordinator=ResearchCoordinator(fetcher=fetch)
        first=asyncio.create_task(coordinator.refresh(enabled=True))
        await started.wait()
        self.assertEqual(await coordinator.refresh(enabled=True),'skipped')
        release.set(); self.assertEqual(await first,'retrieved')

    async def test_cancel_preserves_state_and_unlocks(self):
        started=asyncio.Event()
        async def fetch(): started.set(); await asyncio.Future()
        coordinator=ResearchCoordinator(fetcher=fetch)
        before=coordinator.state
        task=asyncio.create_task(coordinator.refresh(enabled=True))
        await started.wait(); task.cancel()
        with self.assertRaises(asyncio.CancelledError): await task
        self.assertIs(coordinator.state,before)
        self.assertFalse(coordinator._lock.locked())

    async def test_errors_retain_previous_snapshot(self):
        previous=FetchResult((),1,1,'terminal_reported')
        for error, expected in [(SourceHTTPError(429,'3600'),3700),
                                (SourceHTTPError(503),1000),
                                (SourceHTTPError(403),math.inf),
                                (ValueError('bad data'),math.inf), (TimeoutError(),1000)]:
            async def fetch(): raise error
            coordinator=ResearchCoordinator(fetcher=fetch,
                state=RefreshState(last_success=previous,last_success_at=1),clock=lambda:100,
                utcnow=lambda:datetime(2026,9,16,tzinfo=timezone.utc))
            self.assertEqual(await coordinator.refresh(enabled=True),'failed')
            self.assertIs(coordinator.state.last_success,previous)
            self.assertEqual(coordinator.state.last_success_at,1)
            self.assertEqual(coordinator.state.next_attempt_at,expected)

    async def test_unexpected_programming_error_propagates(self):
        async def fetch(): raise RuntimeError('bug')
        coordinator=ResearchCoordinator(fetcher=fetch)
        with self.assertRaises(RuntimeError): await coordinator.refresh(enabled=True)
        self.assertFalse(coordinator._lock.locked())


class CheckpointTests(unittest.TestCase):
    def test_restart_uses_saved_remaining_wait_without_wall_clock(self):
        saved=checkpoint(RefreshState(next_attempt_at=1500,failures=2),now=1000)
        restored=restore_checkpoint(saved,now=10)
        self.assertEqual(restored.next_attempt_at,510)
        self.assertEqual(restored.failures,2)
        self.assertNotIn('last_success',saved)

    def test_manual_stop_and_rounding_survive_restart(self):
        for deadline,expected in [(math.inf,math.inf),(10.1,11)]:
            saved=checkpoint(RefreshState(next_attempt_at=deadline),now=0)
            self.assertEqual(restore_checkpoint(saved,now=0).next_attempt_at,expected)

    def test_invalid_checkpoint_is_not_fresh_start(self):
        for data in (None,{}, {'version':True,'wait_seconds':0,'failures':0},
                     {'version':1,'wait_seconds':-1,'failures':0},
                     {'version':1,'wait_seconds':0,'failures':True}):
            with self.assertRaises(ValueError): restore_checkpoint(data,now=0)

class ReceiptTests(unittest.IsolatedAsyncioTestCase):
    async def test_success_failure_and_restart_receipt_semantics(self):
        now = [100]
        wall = [datetime(2026, 9, 24, 9, tzinfo=timezone.utc)]
        error = [False]
        async def fetch():
            if error[0]:
                raise OSError('offline')
            return FetchResult((), 1, 1, 'terminal_reported')
        coordinator = ResearchCoordinator(fetcher=fetch, clock=lambda: now[0], utcnow=lambda: wall[0])
        self.assertIsNone(coordinator.state.received_at)
        await coordinator.refresh(enabled=True)
        self.assertEqual(coordinator.state.received_at, wall[0])
        original = wall[0]
        now[0] = 1000
        wall[0] = datetime(2026, 9, 23, 9, tzinfo=timezone.utc)
        error[0] = True
        await coordinator.refresh(enabled=True)
        self.assertEqual(coordinator.state.received_at, original)
        self.assertEqual(coordinator.state.last_success_at, 100)
        restored = restore_checkpoint(checkpoint(coordinator.state, now=1000), now=2000)
        self.assertIsNone(restored.received_at)
