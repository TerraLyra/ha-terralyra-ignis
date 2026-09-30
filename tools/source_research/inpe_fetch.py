"""Explicit research fetch of INPE's viewer endpoint; no timer or persistence."""
from urllib.request import HTTPRedirectHandler, Request, build_opener
from inpe_centroids import MAX_BYTES, STATES, parse_centroids

ENDPOINT = 'https://data.inpe.br/queimadas/portal/api/eventos/centroides'


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def fetch_centroids(*, state=None):
    """One request, 30s socket timeout, 8 MiB cap, no redirects or retries.

    This timeout is not an absolute wall-clock deadline. HTTP Date is not a
    source observation/publication timestamp. No custom coordinates are sent.
    """
    if state is not None and (not isinstance(state, str) or state not in STATES):
        raise ValueError('Invalid state')
    url = ENDPOINT if state is None else ENDPOINT + '?uf=' + state
    request = Request(url, headers={'Accept': 'application/json',
                                        'Accept-Encoding': 'identity'})
    with build_opener(_NoRedirect()).open(request, timeout=30) as response:
        if (response.status != 200 or response.headers.get_content_type() != 'application/json'
                or response.headers.get('Content-Encoding', 'identity') != 'identity'):
            raise ValueError('Unexpected INPE representation')
        length = response.headers.get('Content-Length')
        if length is not None and (not length.isascii() or not length.isdecimal()
                                   or int(length) > MAX_BYTES):
            raise ValueError('Invalid/excessive content length')
        payload = response.read(MAX_BYTES + 1)
        if length is not None and len(payload) != int(length):
            raise ValueError('Response length mismatch')
    return parse_centroids(payload, requested_state=state)
