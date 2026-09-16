"""Cancellable research retrieval; no HA enablement or automatic retry."""
from __future__ import annotations

import asyncio

from nifc_fetch import _fetch_steps
from nifc_refresh import SourceHTTPError


async def _read(session, url, byte_limit, timeout):
    import aiohttp

    async with session.get(url, allow_redirects=False,
                           timeout=aiohttp.ClientTimeout(total=timeout),
                           headers={'Accept': 'application/json', 'Accept-Encoding': 'identity'}) as response:
        if response.status != 200:
            raise SourceHTTPError(response.status, response.headers.get('Retry-After'))
        if response.headers.get('Content-Encoding', 'identity') != 'identity':
            raise ValueError('Unexpected HTTP response; automatic retry disabled')
        chunks, size = [], 0
        async for chunk in response.content.iter_chunked(16384):
            size += len(chunk)
            if size > byte_limit:
                raise ValueError('Response byte limit exceeded')
            chunks.append(chunk)
        return b''.join(chunks)


async def fetch_incidents_async(*, reader=None, total_timeout=60, **limits):
    """Overall async deadline covers all requests and body reads.

    Injected readers must cooperate with asyncio cancellation, honor byte caps and
    not block the event loop. Synchronous JSON validation is bounded by input limits
    but cannot be preempted. No retries: 429/5xx abort, never trigger a request loop.
    """
    if type(total_timeout) is not int or total_timeout <= 0:
        raise ValueError('Total timeout must be a positive integer')

    async def drive(read):
        steps = _fetch_steps(**limits)
        try:
            request = next(steps)
            while True:
                payload = await read(*request)
                try:
                    request = steps.send(payload)
                except StopIteration as completed:
                    return completed.value
        finally:
            steps.close()

    async def run():
        if reader is not None:
            return await drive(reader)
        import aiohttp
        async with aiohttp.ClientSession(auto_decompress=False, trust_env=False) as session:
            async def read(*args):
                return await _read(session, *args)
            return await drive(read)

    return await asyncio.wait_for(run(), timeout=total_timeout)
