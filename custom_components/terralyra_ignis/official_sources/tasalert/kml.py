"""Offline TasALERT KML preflight parser. No network or HA side effects."""
from datetime import datetime
import math
from urllib.parse import urlsplit
from defusedxml import ElementTree as ET
from defusedxml.common import DefusedXmlException

NS = {'k': 'http://www.opengis.net/kml/2.2'}
MAX_BYTES = 2 * 1024 * 1024


def timestamp(value):
    """Preserve the supplied offset; never invent record-clock semantics."""
    result = datetime.fromisoformat(value)
    if result.utcoffset() is None:
        raise ValueError('Timestamp requires an explicit offset')
    return result.isoformat()


def parse_kml(raw: bytes):
    """Return a complete validated snapshot or fail; never silently drop records."""
    if not isinstance(raw, bytes) or len(raw) > MAX_BYTES:
        raise ValueError('Bounded byte input required')
    text = raw.decode('utf-8-sig')
    if '<!DOCTYPE' in text.upper() or '<!ENTITY' in text.upper():
        raise ValueError('XML declarations with entities are unsupported')
    try:
        root = ET.fromstring(text, forbid_dtd=True)
    except DefusedXmlException as error:
        raise ValueError("Unsafe XML") from error
    if root.tag != '{http://www.opengis.net/kml/2.2}kml':
        raise ValueError('Expected KML 2.2')
    records, seen = [], set()
    placemarks = root.findall('.//k:Placemark', NS)
    if len(placemarks) > 5000:
        raise ValueError('Too many placemarks')
    for mark in placemarks:
        identifier = mark.get('id')
        if not identifier or not identifier.strip() or identifier in seen:
            raise ValueError('Missing or duplicate placemark ID')
        seen.add(identifier)
        fields = {}
        for data in mark.findall('k:ExtendedData/k:Data', NS):
            name = data.get('name')
            if not name or name in fields:
                raise ValueError('Missing or duplicate field name')
            fields[name] = data.findtext('k:value', default='', namespaces=NS)
        kind = fields.get('feedType')
        if kind not in ('incident', 'burnt-area'):
            raise ValueError('Unreviewed feed type')
        clocks = {key: timestamp(fields[key]) for key in ('created', 'changed') if fields.get(key)}
        url = fields.get('url')
        if url:
            parsed = urlsplit(url)
            if parsed.scheme != 'https' or parsed.hostname != 'alert.tas.gov.au' or parsed.username or parsed.password or parsed.port not in (None, 443):
                raise ValueError('Unsafe source URL')
        points = mark.findall('.//k:Point', NS)
        point = None
        if len(points) > 1 or (kind == 'incident' and len(points) != 1):
            raise ValueError('Incident requires one explicit point')
        if points:
            values = (points[0].findtext('k:coordinates', default='', namespaces=NS)).strip().split(',')
            if len(values) not in (2, 3):
                raise ValueError('Invalid point')
            numbers = list(map(float, values))
            if not all(math.isfinite(n) for n in numbers):
                raise ValueError('Nonfinite coordinates')
            lon, lat = numbers[:2]
            if not (-180 <= lon <= 180 and -90 <= lat <= 90):
                raise ValueError('Coordinates outside range')
            point = {'latitude': lat, 'longitude': lon}
        records.append({'id': identifier, 'name': mark.findtext('k:name', default='', namespaces=NS),
                        'fields': fields, 'record_times': clocks, 'point': point,
                        'has_polygon': bool(mark.findall('.//k:Polygon', NS))})
    return records
