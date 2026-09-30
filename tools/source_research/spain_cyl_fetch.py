"""Explicit date-scoped JCyL research client; no periodic HA requests."""
from datetime import date
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener
from spain_cyl_paging import collect_pages
from spain_cyl_review import MAX_BYTES, inspect_response

ENDPOINT = 'https://analisis.datosabiertos.jcyl.es/api/explore/v2.1/catalog/datasets/incendios-forestales/records'


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def page_url(day, offset, limit):
    if type(day) is not date:
        raise ValueError('Explicit calendar date required')
    if type(offset) is not int or not 0 <= offset < 100 or type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError('Invalid page bounds')
    if offset + limit > 100:
        raise ValueError('Research record limit exceeded')
    return ENDPOINT + '?' + urlencode({
        'where': f"fecha_del_parte=date'{day.isoformat()}'",
        'order_by': 'fecha_del_parte desc,hora_del_parte desc,orden',
        'offset': offset, 'limit': limit,
    })


def _read(url):
    request = Request(url, headers={'Accept':'application/json','Accept-Encoding':'identity'})
    with build_opener(_NoRedirect()).open(request,timeout=30) as response:
        if (response.status != 200 or response.headers.get_content_type() != 'application/json'
                or response.headers.get('Content-Encoding','identity') != 'identity'):
            raise ValueError('Unexpected response representation')
        raw = response.read(MAX_BYTES+1)
    if len(raw)>MAX_BYTES:
        raise ValueError('Response size exceeded')
    return raw


def collect_date(day, *, reader=_read):
    """One capped request (100 rows), with honest partial/empty/error results.

    Refuse automatic pagination: orden is not unique and paging cannot establish
    consistency. A date is a bulletin selection, not a claim of current validity.
    30s is a socket timeout, not a wall-clock deadline. No redirects or retries.
    """
    url = page_url(day,0,100)
    def fetch(offset,limit):
        raw=reader(url)
        review=inspect_response(raw)
        if any(item['source'].get('fecha_del_parte') != day.isoformat() for item in review['results']):
            raise ValueError('Server returned another bulletin date')
        return raw
    result=collect_pages(fetch,page_size=100,max_pages=1)
    result['requested_date']=day.isoformat()
    result['source_url']=ENDPOINT
    result['license_url']='https://creativecommons.org/licenses/by/4.0/'
    result['attribution']='Junta de Castilla y León'
    return result
