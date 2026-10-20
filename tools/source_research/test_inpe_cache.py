from concurrent.futures import ThreadPoolExecutor
from threading import Event
from unittest import TestCase
from unittest.mock import Mock
from inpe_cache import SnapshotCache, RetryPending


class CacheTests(TestCase):
    def test_hourly_reuse_does_not_change_receipt(self):
        now = [0]
        first, second = object(), object()
        collect = Mock(side_effect=[first, second])
        cache = SnapshotCache(['AC'], collect=collect, clock=lambda: now[0], jitter=lambda: 30)
        self.assertIs(cache.get(), first)
        now[0] = 3629
        self.assertIs(cache.get(), first)
        self.assertEqual(collect.call_count, 1)
        now[0] = 3630
        self.assertIs(cache.get(), second)
        self.assertEqual(collect.call_count, 2)

    def test_failure_retains_old_snapshot_without_returning_stale_success(self):
        now = [0]
        first, recovered = object(), object()
        collect = Mock(side_effect=[first, ValueError('invalid payload'), recovered])
        cache = SnapshotCache(['AC'], collect=collect, clock=lambda: now[0], jitter=lambda: 0)
        self.assertIs(cache.get(), first)
        now[0] = 3600
        with self.assertRaises(ValueError): cache.get()
        self.assertIs(cache.last_success, first)
        with self.assertRaises(RetryPending): cache.get()
        self.assertEqual(collect.call_count, 2)
        now[0] = 7200
        self.assertIs(cache.get(), recovered)
        self.assertIsNone(cache.last_error)

    def test_first_failure_is_also_rate_limited(self):
        collect = Mock(side_effect=TimeoutError)
        cache = SnapshotCache(['AC'], collect=collect, clock=lambda: 0, jitter=lambda: 0)
        with self.assertRaises(TimeoutError): cache.get()
        with self.assertRaises(RetryPending): cache.get()
        self.assertIsNone(cache.last_success)
        self.assertEqual(collect.call_count, 1)

    def test_concurrent_consumers_share_one_request(self):
        entered, release = Event(), Event()
        result = object()
        def collect(states):
            entered.set()
            if not release.wait(5): raise TimeoutError()
            return result
        fetch = Mock(side_effect=collect)
        cache = SnapshotCache(['AC'], collect=fetch, jitter=lambda: 0)
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(cache.get)
            self.assertTrue(entered.wait(5))
            second = pool.submit(cache.get)
            release.set()
            self.assertIs(first.result(), result)
            self.assertIs(second.result(), result)
        self.assertEqual(fetch.call_count, 1)

    def test_invalid_scope_or_jitter_never_fetches(self):
        for states in ([], ['AC','AC'], ['xx'], ['AC','AM','BA','SP']):
            with self.assertRaises(ValueError): SnapshotCache(states)
        for jitter in (-1, 61, float('nan'), True):
            collect = Mock()
            cache = SnapshotCache(['AC'], collect=collect, jitter=lambda: jitter)
            with self.assertRaises(ValueError): cache.get()
            collect.assert_not_called()
