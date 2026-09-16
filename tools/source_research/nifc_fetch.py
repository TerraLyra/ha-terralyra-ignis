"""Opt-in bounded research fetch; never imported by the HA integration."""
from __future__ import annotations

from urllib.request import HTTPRedirectHandler, Request, build_opener

from nifc_package import load_module
_query = load_module("query")
FetchResult = _query.FetchResult
_fetch_steps = _query._fetch_steps

ENDPOINT = _query.ENDPOINT

class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def read_url(url, byte_limit, timeout):
    """Bound bytes during reading, refuse redirects and compressed responses.

    Timeout is the socket timeout, not a guaranteed total wall-clock deadline.
    No retries, credentials, user coordinates or persistence.
    """
    request = Request(url, headers={'Accept': 'application/json', 'Accept-Encoding': 'identity'})
    with build_opener(_NoRedirect()).open(request, timeout=timeout) as response:
        if response.status != 200 or response.headers.get('Content-Encoding', 'identity') != 'identity':
            raise ValueError('Unexpected HTTP response')
        payload = response.read(byte_limit + 1)
    if len(payload) > byte_limit:
        raise ValueError('Response byte limit exceeded')
    return payload



def fetch_incidents(*, reader=read_url, **limits) -> FetchResult:
    """Synchronous research API; socket timeout only, no overall deadline."""
    steps = _fetch_steps(**limits)
    try:
        request = next(steps)
        while True:
            request = steps.send(reader(*request))
    except StopIteration as completed:
        return completed.value
    finally:
        steps.close()
