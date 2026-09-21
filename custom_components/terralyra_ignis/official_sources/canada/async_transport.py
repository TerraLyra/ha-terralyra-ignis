"""Research async transport: bounded download, no redirects, no HA activation."""
import asyncio
from urllib.parse import urlencode
import aiohttp
from .fetch import ENDPOINT, MAX_BYTES, MAX_RECORDS, decode_response


async def read_json(session, url, *, seconds=30, max_bytes=MAX_BYTES):
    # Explicit outer deadline avoids socket-idle timers resetting on slow trickles.
    async with asyncio.timeout(seconds):
        async with session.get(url, allow_redirects=False,
                timeout=aiohttp.ClientTimeout(total=seconds),
                auto_decompress=False, headers={'Accept-Encoding':'identity'}) as response:
            if response.status != 200:
                response.raise_for_status()
                raise ValueError('Unexpected HTTP status')
            if response.content_type != 'application/json':
                raise ValueError('Expected JSON')
            if response.headers.get('Content-Encoding','identity').lower() != 'identity':
                raise ValueError('Unexpected content encoding')
            if response.content_length is not None and response.content_length > max_bytes:
                raise ValueError('Response byte limit exceeded')
            data=bytearray()
            async for chunk in response.content.iter_chunked(16384):
                if len(data)+len(chunk)>max_bytes:
                    raise ValueError('Response byte limit exceeded')
                data.extend(chunk)
    return bytes(data)


async def fetch_async(session):
    params=dict(service='WFS',version='2.0.0',request='GetFeature',
        typeNames='public:cwfif_national_activefires',outputFormat='application/json',
        count=MAX_RECORDS,srsName='EPSG:4326',sortBy='national_fire_id A',
        CQL_FILTER='record_start<=now() AND record_end>now()')
    raw=await read_json(session,ENDPOINT+'?'+urlencode(params))
    return decode_response(raw)
