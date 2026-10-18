"""Failure details survive restart without persisting server text."""
import unittest
from dataclasses import replace
from nifc_package import load_module

coordinator = load_module('coordinator')
refresh = load_module('refresh')

class FailureDetailsTests(unittest.IsolatedAsyncioTestCase):
    async def capture(self, error):
        async def fetch():
            raise error
        instance = coordinator.NifcCoordinator(fetcher=fetch, clock=lambda: 100)
        self.assertEqual(await instance.refresh(enabled=True), 'failed')
        return instance.state

    async def test_validation_roundtrip_preserves_recovery_bound(self):
        state = await self.capture(ValueError('Unexpected layer schema'))
        data = coordinator.checkpoint(state, now=100)
        restored = coordinator.restore_checkpoint(data, now=300)
        self.assertEqual(restored.failure_reason, 'Unexpected layer schema')
        self.assertEqual(restored.resume_after_review_at, 1200)
        self.assertEqual(restored.next_attempt_at, float('inf'))

    async def test_unknown_exception_text_is_not_persisted(self):
        state = await self.capture(ValueError('private server payload and credentials'))
        data = coordinator.checkpoint(state, now=100)
        self.assertNotIn('private', str(data))
        self.assertEqual(state.failure_reason, 'Unrecognized validation failure')

    async def test_http_status_and_wait_survive_restart(self):
        state = await self.capture(refresh.SourceHTTPError(429, '7200'))
        restored = coordinator.restore_checkpoint(coordinator.checkpoint(state, now=100), now=200)
        self.assertEqual(restored.failure_http_status, 429)
        self.assertEqual(restored.next_attempt_at, 7400)

    async def test_timeout_does_not_retain_previous_http_status(self):
        state = await self.capture(TimeoutError('private'))
        self.assertEqual(state.failure_reason, 'Request timed out')
        self.assertIsNone(state.failure_http_status)

    def test_corrupt_diagnostic_is_rejected(self):
        data = dict(version=3, cooldown=dict(version=1, wait_seconds=900, failures=1),
                    failure_reason='private', http_status=None)
        with self.assertRaises(ValueError):
            coordinator.restore_checkpoint(data, now=100)

    def test_legacy_checkpoint_remains_supported(self):
        state = coordinator.restore_checkpoint(dict(version=1, wait_seconds=900, failures=1), now=100)
        self.assertIsNone(state.failure_reason)
        self.assertEqual(state.next_attempt_at, 1000)

    async def test_controlled_recovery_keeps_reason_until_success(self):
        from test_nifc_async_storage import Store
        stored_class = load_module('stored_coordinator').NifcStoredCoordinator
        state = await self.capture(ValueError('Unexpected layer schema'))
        raw = Store()
        raw.data = coordinator.checkpoint(state, now=100)
        now = [200]
        async def fetch():
            return load_module('query').FetchResult((), 1, 1, 'terminal_reported')
        stored = stored_class(raw, clock=lambda: now[0], fetcher=fetch)
        await stored.setup()
        self.assertEqual(stored.diagnostics()['last_failure_reason'], 'Unexpected layer schema')
        await stored.recover()
        self.assertEqual(await stored.refresh(enabled=True), 'skipped')
        self.assertEqual(stored.state.next_attempt_at, 1100)
        now[0] = 1100
        self.assertEqual(await stored.refresh(enabled=True), 'retrieved')
        self.assertIsNone(stored.diagnostics()['last_failure_reason'])
        self.assertEqual(raw.data['version'], 1)
