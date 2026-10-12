"""Async research client using a caller-owned aiohttp-compatible session."""
import asyncio
from datetime import datetime, UTC
from tasalert_engine import advance
from tasalert_fetch import URL
from tasalert_kml import MAX_BYTES
from tasalert_policy import request_headers


async def fetch_once(engine, session, *, clock=lambda: datetime.now(UTC), total_timeout=30, transport_errors=(OSError,)):
    """No retries/redirects. Caller serializes calls and persists returned state.

    Session must use verified TLS and raise_for_status=False. For aiohttp, pass
    transport_errors=(aiohttp.ClientError, OSError) to classify payload errors. Cancellation is
    propagated, never converted to success/failure or committed by this function.
    The timeout covers connection, headers and streamed body, not only inactivity.
    """
    if total_timeout<=0:raise ValueError('Positive deadline required')
    now=clock()
    if now.utcoffset() is None:raise ValueError('Aware receipt clock required')
    if engine.response.next_attempt and now<engine.response.next_attempt:return engine
    headers={'User-Agent':'TerraLyra-IGNIS-research','Accept-Encoding':'identity',
             'Accept':'application/vnd.google-earth.kml+xml, application/xml, text/xml',
             **request_headers(engine.response)}
    try:
        async with asyncio.timeout(total_timeout):
            async with session.get(URL,headers=headers,allow_redirects=False,
                                   auto_decompress=False,raise_for_status=False) as response:
                retry=response.headers.get('Retry-After')
                if response.status!=200:return advance(engine,now,response.status,retry_after=retry)
                length=response.headers.get('Content-Length')
                if (response.headers.get('Content-Encoding','identity').lower() not in ('identity','')
                    or (length is not None and (not length.isdigit() or int(length)>MAX_BYTES))):
                    return advance(engine,now,503,retry_after=retry)
                body=bytearray()
                async for chunk in response.content.iter_chunked(65536):
                    if len(body)+len(chunk)>MAX_BYTES:return advance(engine,now,503,retry_after=retry)
                    body.extend(chunk)
                if length is not None and len(body)!=int(length):return advance(engine,now,503,retry_after=retry)
                return advance(engine,now,200,bytes(body),etag=response.headers.get('ETag'),retry_after=retry)
    except (TimeoutError, *transport_errors):
        return advance(engine,now,503)
