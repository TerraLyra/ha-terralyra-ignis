"""Explicit research-only GWIS cycle, with no HA configuration or persistence."""
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
import time
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from gwis_point import ENDPOINT, MAX_BYTES, PointEvidence, parse_point, point_url


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def read_point(url: str) -> bytes:
    """One bounded request; no redirects, cookies, auth or implicit retries.

    Socket timeout is 20s; this is not a total wall-clock deadline.
    """
    parsed = urlsplit(url)
    if (parsed.scheme != 'https' or parsed.netloc != urlsplit(ENDPOINT).netloc
            or parsed.path != '/gwis' or parsed.fragment):
        raise ValueError('Unexpected GWIS endpoint')
    request = Request(url, headers={'Accept': 'text/html', 'Accept-Encoding': 'identity'})
    with build_opener(_NoRedirect()).open(request, timeout=20) as response:
        if (response.status != 200 or response.headers.get_content_type() != 'text/html'
                or response.headers.get('Content-Encoding', 'identity') != 'identity'):
            raise ValueError('Unexpected HTTP representation')
        payload = response.read(MAX_BYTES + 1)
    if len(payload) > MAX_BYTES:
        raise ValueError('Response too large')
    return payload


@dataclass(frozen=True)
class RequestedDay:
    requested_date: date
    evidence: PointEvidence


@dataclass(frozen=True)
class ResearchCycle:
    latitude: float
    longitude: float
    retrieved_at: datetime
    days: tuple[RequestedDay, ...]
    model_issued_at: None = None
    returned_valid_date: None = None
    production_ready: bool = False


def fetch_cycle(latitude, longitude, first_day, *, days=10, reader=read_point,
                sleep=time.sleep, now=lambda: datetime.now(timezone.utc)):
    """At most ten requests, 1s spacing, abort on errors; no partial success.

    Only current UTC day through day +9 is accepted. Date checks are repeated
    after the cycle so crossing midnight cannot silently change its context.
    Empty/nodata responses remain evidence of missing data, never zero risk.
    """
    if type(days) is not int or not 1 <= days <= 10 or type(first_day) is not date:
        raise ValueError('Invalid date window')
    start = now()
    if start.tzinfo is None or start.utcoffset() != timedelta(0):
        raise ValueError('UTC clock required')
    if first_day < start.date() or first_day + timedelta(days=days-1) > start.date()+timedelta(days=9):
        raise ValueError('Outside research forecast horizon')
    urls = [point_url(latitude, longitude, first_day+timedelta(days=i)) for i in range(days)]
    results = []
    for i, url in enumerate(urls):
        if i:
            sleep(1)
        # HTTP errors (including 429/503) propagate: never retry peers in this cycle.
        payload = reader(url)
        results.append(RequestedDay(first_day+timedelta(days=i), parse_point(payload)))
    end = now()
    if end.tzinfo is None or end.utcoffset() != timedelta(0) or end < start or end.date() != start.date():
        raise ValueError('Clock/date changed during cycle')
    return ResearchCycle(latitude, longitude, end, tuple(results))
