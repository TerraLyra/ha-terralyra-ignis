"""Opt-in research KML client. Fixed HTTPS endpoint, no background polling."""
from datetime import datetime, UTC
import socket
from http.client import HTTPException
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener, HTTPRedirectHandler
from tasalert_engine import advance
from tasalert_kml import MAX_BYTES
from tasalert_policy import request_headers

URL = 'https://alert.tas.gov.au/data/incidents-and-messages.kml'
TIMEOUT = 20  # Socket-operation timeout, not a total wall-clock deadline.


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def fetch_once(engine, *, clock=lambda: datetime.now(UTC), opener=None):
    """One due request; return a new state, leave persistence to the caller.

    The caller serializes fetch/save operations. No credentials, no redirects,
    no automatic retries, no linked event-page requests. TLS verification uses
    the standard verified HTTPS handler. HTTP errors honor response Retry-After.
    """
    now=clock()
    if now.utcoffset() is None:raise ValueError('Aware clock required')
    if engine.response.next_attempt and now<engine.response.next_attempt:
        return engine
    request=Request(URL,headers={
        'User-Agent':'TerraLyra-IGNIS-research',
        'Accept':'application/vnd.google-earth.kml+xml, application/xml, text/xml',
        'Accept-Encoding':'identity', **request_headers(engine.response)})
    transport=opener if opener is not None else build_opener(NoRedirects())
    try:
        try:
            response=transport.open(request,timeout=TIMEOUT)
        except HTTPError as error:
            response=error
        with response:
            status=response.code
            headers=response.headers
            retry=headers.get('Retry-After')
            if status!=200:
                return advance(engine,now,status,retry_after=retry)
            if headers.get('Content-Encoding','identity').lower() not in ('identity',''):
                return advance(engine,now,503,retry_after=retry)
            length=headers.get('Content-Length')
            if length is not None and (not length.isdigit() or int(length)>MAX_BYTES):
                return advance(engine,now,503,retry_after=retry)
            body=response.read(MAX_BYTES+1)
            if len(body)>MAX_BYTES or (length is not None and len(body)!=int(length)):
                return advance(engine,now,503,retry_after=retry)
            return advance(engine,now,200,body,etag=headers.get('ETag'),retry_after=retry)
    except (URLError, OSError, socket.timeout, HTTPException):
        return advance(engine,now,503)
