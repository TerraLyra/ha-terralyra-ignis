"""Async, bounded state fetch for HA's shared HTTP session; no automatic retries."""
import asyncio
from .centroids import MAX_BYTES, STATES, parse_centroids

URL = 'https://data.inpe.br/queimadas/portal/api/eventos/centroides'


class FetchError(ValueError):
    """Fixed diagnostic code; do not expose raw upstream bodies."""


async def fetch_state(session, state, *, total_timeout=30):
    """Caller must use verified TLS and enforce shared hourly scheduling.

    Empty valid FeatureCollection is a successful returned inventory. It is not
    evidence of completeness, absence of fires or extinguishment of old records.
    """
    if not isinstance(state, str) or state not in STATES:
        raise ValueError('Invalid state')
    if total_timeout <= 0:
        raise ValueError('Positive deadline required')
    async with asyncio.timeout(total_timeout):
        async with session.get(URL, params={'id_tipo_reg': '1', 'uf': state.lower()},
                headers={'Accept':'application/json', 'Accept-Encoding':'identity'},
                allow_redirects=False, auto_decompress=False, raise_for_status=False) as response:
            if response.status != 200:
                raise FetchError('http_error')
            content_type = response.headers.get('Content-Type', '').split(';')[0].strip().lower()
            if content_type != 'application/json':
                raise FetchError('unexpected_content_type')
            if response.headers.get('Content-Encoding', 'identity').lower() != 'identity':
                raise FetchError('unexpected_encoding')
            length = response.headers.get('Content-Length')
            if length is not None and (not length.isascii() or not length.isdecimal() or int(length)>MAX_BYTES):
                raise FetchError('invalid_content_length')
            body = bytearray()
            async for chunk in response.content.iter_chunked(65536):
                if len(body)+len(chunk)>MAX_BYTES:
                    raise FetchError('response_too_large')
                body.extend(chunk)
            if length is not None and len(body)!=int(length):
                raise FetchError('truncated_response')
            return parse_centroids(bytes(body), requested_state=state)
