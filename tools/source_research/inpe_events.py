"""Offline INPE Queimadas event inventory; never a production HA provider.

One record per event Folder, not per Placemark. Descriptions remain untrusted
source text. No embedded links are followed and no HTML is rendered.
"""
from dataclasses import dataclass
from io import StringIO
import math
import re
import xml.etree.ElementTree as ET

NS = '{http://www.opengis.net/kml/2.2}'
MAX_BYTES = 32 * 1024 * 1024
MAX_EVENTS = 20_000
EVENT_NAME = re.compile(r'Evento ([0-9]{1,20}) – (.{1,200})\Z')
ATTRIBUTION = 'INPE / Programa Queimadas — Eventos de Fogo'
LICENSE_URL = 'https://creativecommons.org/licenses/by-sa/4.0/'


class InvalidEvents(ValueError):
    """Reject the whole inventory; an invalid document is not an empty feed."""


@dataclass(frozen=True)
class Event:
    source_id: str
    category: str
    longitude: float
    latitude: float
    description_raw: str
    geometry_present: bool
    collection: str
    # Active/observation are collection labels, not confirmed fire conditions.
    provisional: bool = True
    observed_at: None = None


def _text(element, tag):
    children = element.findall(NS + tag)
    if len(children) != 1 or len(children[0]):
        raise InvalidEvents('Missing, duplicate or nested text field')
    return children[0].text or ''


def _event(folder, collection):
    match = EVENT_NAME.fullmatch(_text(folder, 'name'))
    if not match:
        raise InvalidEvents('Unexpected event name')
    marks = folder.findall(NS + 'Placemark')
    points = [p for p in marks if p.find(NS + 'Point') is not None]
    if len(points) != 1:
        raise InvalidEvents('Expected one event representative point')
    point_mark = points[0]
    if len(point_mark.findall(NS + 'Point')) != 1:
        raise InvalidEvents('Duplicate point')
    point = point_mark.find(NS + 'Point')
    coords = _text(point, 'coordinates').strip().split(',')
    if len(coords) not in (2, 3):
        raise InvalidEvents('Invalid point coordinates')
    try:
        numbers = tuple(float(v) for v in coords)
    except ValueError as exc:
        raise InvalidEvents('Non-numeric point') from exc
    if not all(math.isfinite(v) for v in numbers):
        raise InvalidEvents('Non-finite point')
    lon, lat = numbers[:2]
    if not -180 <= lon <= 180 or not -90 <= lat <= 90:
        raise InvalidEvents('Point outside global bounds')
    description = _text(point_mark, 'description')
    if not description.strip() or len(description) > 65_536:
        raise InvalidEvents('Missing or excessive description')
    return Event(match[1], match[2], lon, lat, description,
                 any(p.find(NS + 'Polygon') is not None for p in marks), collection)


def inspect_events(payload: bytes, *, collection: str) -> tuple[Event, ...]:
    """Bounded UTF-8 KML inspection, no fetching, merging or history changes.

    Point coordinates are provider representative locations, not measured fire
    boundaries. Source IDs are only unique within this snapshot; persistence
    and reuse across dates are not established. Unknown categories are kept.
    """
    if collection not in ('active', 'observation'):
        raise InvalidEvents('Unknown source collection')
    if not isinstance(payload, bytes) or not payload or len(payload) > MAX_BYTES:
        raise InvalidEvents('Invalid payload size/type')
    try:
        text = payload.decode('utf-8-sig')
    except UnicodeDecodeError as exc:
        raise InvalidEvents('Expected UTF-8') from exc
    if '\x00' in text or re.search(r'<!\s*(DOCTYPE|ENTITY)', text, re.I):
        raise InvalidEvents('XML declarations are forbidden')
    depth = nodes = 0
    records = []
    ids = set()
    try:
        for action, element in ET.iterparse(StringIO(text), events=('start', 'end')):
            if action == 'start':
                depth += 1
                nodes += 1
                if depth == 1 and element.tag != NS + 'kml':
                    raise InvalidEvents('Expected KML root')
                if depth > 32 or nodes > 500_000:
                    raise InvalidEvents('XML complexity limit exceeded')
                if element.tag in (NS + 'NetworkLink', NS + 'NetworkLinkControl'):
                    raise InvalidEvents('Network-linked inventory unsupported')
            else:
                if element.tag == NS + 'Folder':
                    name = element.findtext(NS + 'name', '')
                    if name.startswith('Evento '):
                        record = _event(element, collection)
                        if record.source_id in ids or len(records) >= MAX_EVENTS:
                            raise InvalidEvents('Duplicate ID or event limit exceeded')
                        ids.add(record.source_id)
                        records.append(record)
                        element.clear()
                depth -= 1
    except ET.ParseError as exc:
        raise InvalidEvents('Malformed XML') from exc
    # An empty arbitrary KML cannot establish zero events or successful coverage.
    if not records:
        raise InvalidEvents('No recognized events; empty-product semantics unverified')
    return tuple(records)
