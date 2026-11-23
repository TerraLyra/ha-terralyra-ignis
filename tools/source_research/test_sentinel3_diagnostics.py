"""Offline transport-to-provider diagnostics without loading Home Assistant."""
import asyncio
import sys
import types
import unittest
from pathlib import Path
from datetime import timedelta

root = Path(__file__).resolve().parents[2] / 'custom_components/terralyra_ignis'
for name, path in [('sentinel_diag', root), ('sentinel_diag.providers', root / 'providers')]:
    package = types.ModuleType(name)
    package.__path__ = [str(path)]
    sys.modules[name] = package
from aiohttp import ClientConnectionError
from sentinel_diag.products.sentinel3 import Sentinel3Client
from sentinel_diag.providers.sentinel3 import Sentinel3ActiveFireProvider
from sentinel_diag.providers.base import ActiveFireProviderError, safe_diagnostic_code


class Response:
    headers = {'Retry-After': '120'}
    def __init__(self, status):
        self.status = status
    async def __aenter__(self):
        return self
    async def __aexit__(self, *args):
        pass


class Session:
    def __init__(self, outcome):
        self.outcome = outcome
    def get(self, *args, **kwargs):
        if isinstance(self.outcome, Exception):
            raise self.outcome
        return Response(self.outcome)


class DiagnosticsTests(unittest.TestCase):
    def test_transport_failure_codes_and_retry(self):
        for satellite in ('S3A', 'S3B'):
            for outcome, code, failure, retry in (
                (ClientConnectionError('private token'), 'network_error', 'service_outage', None),
                (TimeoutError('private token'), 'timeout', 'timeout', None),
                (503, 'server_error', 'service_outage', timedelta(seconds=120)),
                (429, 'rate_limited', 'rate_limit', timedelta(seconds=120)),
                (403, 'invalid_response', 'invalid_response', None),
                (200, 'invalid_response', 'invalid_response', None),
            ):
                with self.subTest(satellite=satellite, code=code):
                    provider = Sentinel3ActiveFireProvider(
                        Sentinel3Client(Session(outcome)), satellite=satellite,
                        bounds=((18., 46., 20., 48.),))
                    with self.assertRaises(ActiveFireProviderError) as caught:
                        asyncio.run(provider.async_fetch_latest())
                    self.assertEqual(caught.exception.diagnostic_code, 'sentinel3_' + code)
                    self.assertEqual(caught.exception.failure_type, failure)
                    self.assertEqual(caught.exception.retry_after, retry)
                    self.assertNotIn('private', caught.exception.diagnostic_code)

    def test_unknown_codes_are_not_exported(self):
        self.assertIsNone(safe_diagnostic_code('sentinel3_private token'))


class ParserThreadTests(unittest.IsolatedAsyncioTestCase):
    async def test_parser_runs_off_event_loop(self):
        import json
        from datetime import UTC, datetime
        from threading import get_ident
        from unittest.mock import AsyncMock, patch
        from sentinel_diag.products import sentinel3

        now = datetime(2026, 9, 7, 12, tzinfo=UTC)
        body = json.dumps({"type":"FeatureCollection", "features":[],
            "numberMatched":0, "numberReturned":0,
            "timeStamp":"2026-09-07T12:00:02Z"}).encode()
        client = Sentinel3Client(None)
        original = sentinel3.parse_sentinel3_geojson
        loop_thread = get_ident()
        threads = []
        def parse(*args, **kwargs):
            threads.append(get_ident())
            return original(*args, **kwargs)
        with patch.object(client, '_async_get', AsyncMock(return_value=body)):
            with patch.object(sentinel3, 'parse_sentinel3_geojson', parse):
                result = await client.async_area(satellite='S3A',
                    bounds=((18., 46., 20., 48.),), now=now)
        self.assertEqual(result.detections, ())
        self.assertEqual(len(threads), 1)
        self.assertNotEqual(threads[0], loop_thread)


if __name__ == '__main__':
    unittest.main()
