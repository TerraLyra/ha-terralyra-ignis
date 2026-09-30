"""Bounded offline inspection of the official viewer's INPE centroid response.

No production imports, timestamp inference, incident closure or deduplication
against FIRMS. Centroid proximity is not perimeter proximity.
"""
from dataclasses import dataclass
import json
import math

MAX_BYTES = 8 * 1024 * 1024
MAX_RECORDS = 20_000
STATES = frozenset("AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split())


class InvalidCentroids(ValueError):
    """A failed inventory must not replace previous data with zero events."""


@dataclass(frozen=True)
class Centroid:
    source_id: int
    longitude: float
    latitude: float
    category: str
    status: str
    area_ha: float | None
    duration_days: float | None
    state: str
    municipality: str
    states: tuple[str, ...] = ()
    observed_at: None = None
    provisional: bool = True


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise InvalidCentroids('Duplicate JSON key')
        result[key] = value
    return result


def _constant(value):
    raise InvalidCentroids('Non-finite JSON constant')


def _number(value):
    if type(value) not in (int, float):
        raise InvalidCentroids('Expected number')
    try:
        number = float(value)
    except (OverflowError, ValueError) as exc:
        raise InvalidCentroids('Number out of range') from exc
    if not math.isfinite(number):
        raise InvalidCentroids('Expected finite number')
    return number


def _optional_positive(value):
    if value is None:
        return None
    number = _number(value)
    if number < 0:
        raise InvalidCentroids('Negative measurement')
    return number


def _string(value):
    if not isinstance(value, str) or not value.strip() or len(value) > 256:
        raise InvalidCentroids('Invalid source label')
    return value


def parse_centroids(payload: bytes, *, requested_state=None) -> tuple[Centroid, ...]:
    if requested_state is not None and (not isinstance(requested_state, str) or requested_state not in STATES):
        raise InvalidCentroids("Invalid requested state")
    if not isinstance(payload, bytes) or not 0 < len(payload) <= MAX_BYTES:
        raise InvalidCentroids('Payload size/type')
    try:
        root = json.loads(payload.decode('utf-8'), object_pairs_hook=_pairs,
                          parse_constant=_constant)
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise InvalidCentroids('Invalid JSON') from exc
    if not isinstance(root, dict) or root.get('type') != 'FeatureCollection':
        raise InvalidCentroids('Expected feature collection')
    if 'crs' in root or any(k in root for k in ('error', 'next', 'links')):
        raise InvalidCentroids('Unsupported CRS/error/paging envelope')
    features = root.get('features')
    if not isinstance(features, list) or not 0 < len(features) <= MAX_RECORDS:
        raise InvalidCentroids('Empty or excessive inventory; completeness unknown')
    records, ids = [], set()
    for feature in features:
        if not isinstance(feature, dict) or feature.get('type') != 'Feature':
            raise InvalidCentroids('Invalid feature')
        geometry, props = feature.get('geometry'), feature.get('properties')
        if (not isinstance(geometry, dict) or geometry.get('type') != 'Point'
                or not isinstance(props, dict)):
            raise InvalidCentroids('Expected point and properties')
        coords = geometry.get('coordinates')
        if not isinstance(coords, list) or len(coords) != 2:
            raise InvalidCentroids('Expected lon/lat pair')
        lon, lat = map(_number, coords)
        if not -180 <= lon <= 180 or not -90 <= lat <= 90:
            raise InvalidCentroids('Coordinate bounds')
        identifier = props.get('id_evento')
        if type(identifier) is not int or not 0 < identifier < 2**63 or identifier in ids:
            raise InvalidCentroids('Invalid or duplicate event ID')
        ids.add(identifier)
        states = props.get('estados', [])
        if (not isinstance(states, list) or len(states) > len(STATES)
                or any(not isinstance(v, str) or v not in STATES for v in states)
                or len(set(states)) != len(states)):
            raise InvalidCentroids('Invalid state membership')
        if requested_state is not None and requested_state not in states:
            raise InvalidCentroids('Response does not confirm requested state')
        records.append(Centroid(identifier, lon, lat,
                                _string(props.get('tipo')), _string(props.get('status')),
                                _optional_positive(props.get('area_ha')),
                                _optional_positive(props.get('duracao_dias')),
                                _string(props.get('estado')), _string(props.get('municipio')),
                                tuple(sorted(states))))
    return tuple(records)


def compare_kml(records, events):
    """Diagnostic overlap only; no merge, deletion, or lifecycle decision."""
    by_id = {str(r.source_id): r for r in records}
    event_ids = {e.source_id for e in events}
    shared = event_ids & by_id.keys()
    return {'centroids': len(records), 'kml_events': len(events),
            'shared_ids': len(shared), 'only_centroids': len(by_id.keys()-event_ids),
            'only_kml': len(event_ids-by_id.keys()),
            'category_mismatches': sum(by_id[e.source_id].category != e.category
                                       for e in events if e.source_id in shared)}
