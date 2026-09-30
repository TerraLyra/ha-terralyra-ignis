"""Bounded, offline parsing and request planning for GWIS point evidence.

Never imported by HA. Requested date is not a returned product/issuance date.
No risk-class conversion, TIFF fallback or automatic production eligibility.
"""
from dataclasses import dataclass
from datetime import date
from html.parser import HTMLParser
import math
import re
from urllib.parse import urlencode

ENDPOINT = 'https://maps.effis.emergency.copernicus.eu/gwis'
MAX_BYTES = 65_536
LABELS = ('Fire Weather Index (FWI)', 'Initial Spread Index (ISI)',
          'Build Up Index (BUI)', 'Fine Fuel Moisture Code (FFMC)',
          'Duff Moisture Code (DMC)', 'Drought Code (DC)',
          'Anomaly Index', 'Ranking Index')
NUMBER = re.compile(r'-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\Z')


class InvalidPoint(ValueError):
    """Unexpected upstream representation; do not interpret as low risk."""


@dataclass(frozen=True)
class PointEvidence:
    status: str
    fwi: float | None
    raw_values: tuple[tuple[str, str], ...] = ()


class _Table(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.rows = []
        self.cells = []
        self.text = ''
        self.heading = ''
        self.sections = []

    def handle_starttag(self, tag, attrs):
        parent = self.stack[-1] if self.stack else None
        allowed = {None: {'h2', 'table'}, 'table': {'tr'}, 'tr': {'td'}}
        if tag not in allowed.get(parent, set()):
            raise InvalidPoint('Unexpected HTML structure')
        if attrs != ([('id', 'main')] if tag == 'table' else []):
            raise InvalidPoint('Unexpected HTML attributes')
        if parent is None:
            self.sections.append(tag)
            if self.sections not in (['h2'], ['h2', 'table']):
                raise InvalidPoint('Duplicate or reordered table')
        self.stack.append(tag)
        if tag == 'tr':
            self.cells = []
        if tag == 'td':
            self.text = ''

    def handle_endtag(self, tag):
        if not self.stack or self.stack.pop() != tag:
            raise InvalidPoint('Unbalanced HTML')
        if tag == 'td':
            self.cells.append(self.text.strip())
        if tag == 'tr':
            if len(self.cells) != 2 or len(self.rows) >= len(LABELS):
                raise InvalidPoint('Unexpected table shape')
            self.rows.append(tuple(self.cells))

    def handle_data(self, data):
        if self.stack and self.stack[-1] == 'td':
            self.text += data
        elif self.stack and self.stack[-1] == 'h2':
            self.heading += data
        elif data.strip():
            raise InvalidPoint('Unexpected HTML text')

    def handle_comment(self, data):
        raise InvalidPoint('Unexpected HTML comment')

    def handle_decl(self, decl):
        raise InvalidPoint('Unexpected HTML declaration')

    def handle_pi(self, data):
        raise InvalidPoint('Unexpected processing instruction')

    def unknown_decl(self, data):
        raise InvalidPoint('Unexpected declaration')


def parse_point(payload: bytes) -> PointEvidence:
    """Keep valid zero distinct from empty reply and observed -9999 sentinel."""
    if not isinstance(payload, bytes) or len(payload) > MAX_BYTES:
        raise InvalidPoint('Expected bounded bytes')
    try:
        source = payload.decode('utf-8')
    except UnicodeDecodeError as exc:
        raise InvalidPoint('Expected UTF-8') from exc
    if not source.strip():
        return PointEvidence('no_feature', None)
    if '\x00' in source or '<!' in source or '<?' in source:
        raise InvalidPoint('Unsupported declaration or encoding')
    parser = _Table()
    try:
        parser.feed(source)
        parser.close()
    except (ValueError, AssertionError) as exc:
        raise InvalidPoint('Malformed point response') from exc
    if (parser.stack or parser.sections != ['h2', 'table'] or
            parser.heading.strip() != 'Fire Danger' or
            tuple(row[0] for row in parser.rows) != LABELS):
        raise InvalidPoint('Incomplete or unexpected point table')
    for label, value in parser.rows:
        if not NUMBER.fullmatch(value) or not math.isfinite(float(value)):
            raise InvalidPoint('Non-finite or malformed value')
        if label != 'Anomaly Index' and float(value) < 0 and float(value) != -9999:
            raise InvalidPoint('Unexpected negative index')
    raw = tuple(parser.rows)
    fwi = float(raw[0][1])
    if fwi == -9999:
        return PointEvidence('nodata', None, raw)
    return PointEvidence('numeric_evidence', fwi, raw)


def point_url(latitude: float, longitude: float, requested_date: date) -> str:
    """WMS 1.1.1 uses longitude/latitude order, with a centred odd pixel grid.

    Restrict the research query to non-polar, non-antimeridian points. These
    bounds are request geometry guards, not a product coverage assertion.
    """
    for value, limit in ((latitude, 85), (longitude, 179.9)):
        if type(value) not in (int, float) or not math.isfinite(value) or abs(value) > limit:
            raise ValueError('Unsupported research point')
    if type(requested_date) is not date:
        raise ValueError('Expected explicit date')
    bbox = ','.join(format(v, '.10f') for v in
                    (longitude - .05, latitude - .05, longitude + .05, latitude + .05))
    return ENDPOINT + '?' + urlencode(dict(SERVICE='WMS', VERSION='1.1.1',
        REQUEST='GetFeatureInfo', LAYERS='ecmwf.query', QUERY_LAYERS='ecmwf.query',
        STYLES='', SRS='EPSG:4326', BBOX=bbox, WIDTH=101, HEIGHT=101,
        X=50, Y=50, INFO_FORMAT='text/html', TIME=requested_date.isoformat(), FEATURE_COUNT=1))
