import asyncio
import unittest
from unittest.mock import patch

from nifc_async import fetch_incidents_async
from test_nifc_fetch import encoded


class AsyncFetchTests(unittest.IsolatedAsyncioTestCase):
    async def test_multiple_pages_share_validation(self):
        responses = iter([encoded(more=True), encoded(2)])
        async def reader(*args): return next(responses)
        result = await fetch_incidents_async(reader=reader)
        self.assertEqual(len(result.records), 2)
        self.assertEqual(result.page_count, 2)

    async def test_external_cancellation_closes_reader(self):
        started, closed = asyncio.Event(), asyncio.Event()
        async def reader(*args):
            started.set()
            try: await asyncio.Future()
            finally: closed.set()
        task = asyncio.create_task(fetch_incidents_async(reader=reader))
        await started.wait()
        task.cancel()
        with self.assertRaises(asyncio.CancelledError): await task
        self.assertTrue(closed.is_set())

    async def test_overall_deadline_cancels_slow_body(self):
        closed = asyncio.Event()
        async def reader(*args):
            try: await asyncio.Future()
            finally: closed.set()
        # Exercise the real timeout implementation with a shorter test duration.
        real_wait_for = asyncio.wait_for
        async def fast_wait_for(awaitable, timeout):
            self.assertEqual(timeout, 60)
            return await real_wait_for(awaitable, timeout=0.01)
        with patch('nifc_async.asyncio.wait_for', fast_wait_for):
            with self.assertRaises(asyncio.TimeoutError):
                await fetch_incidents_async(reader=reader)
        self.assertTrue(closed.is_set())

    async def test_failure_does_not_retry_or_return_partial_records(self):
        calls = []
        async def reader(*args):
            calls.append(args)
            if len(calls) == 1: return encoded(more=True)
            raise OSError('synthetic failure')
        with self.assertRaises(OSError): await fetch_incidents_async(reader=reader)
        self.assertEqual(len(calls), 2)

    async def test_invalid_budgets_never_request(self):
        async def reader(*args): self.fail('Unexpected request')
        for limits in ({'total_timeout':True}, {'total_timeout':0}, {'max_pages':0}):
            with self.assertRaises(ValueError): await fetch_incidents_async(reader=reader, **limits)
