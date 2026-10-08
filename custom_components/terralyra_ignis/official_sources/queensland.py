"""Bounded offline QFD mixed incident/warning parser. No matching or alerts."""
from datetime import UTC, datetime
from html import unescape
import json
import math
import re

from .models import GeometryRole, OfficialGeometry, OfficialReport, ParsedReports, RecordKind

MAX_BYTES = 2 * 1024 * 1024
MAX_ITEMS = 2000
MAX_VERTICES = 10000
PUBLIC_URL = "https://www.fire.qld.gov.au/Current-Incidents"
ATTRIBUTION = "Queensland Fire Department; Creative Commons Attribution 4.0"
WARNING_LEVELS = {"Advice", "Watch and Act", "Emergency Warning"}
FIRE_TYPES = {"FIRE VEGETATION", "FIRE PERMITTED BURN"}


def _text(value, *, required=False, limit=1000):
    if not isinstance(value, str) or len(value) > limit:
        raise ValueError("Invalid QFD text")
    result = " ".join(re.sub(r"<[^>]*>", "", unescape(value)).split())
    if required and not result:
        raise ValueError("Missing QFD text")
    return result


def _optional_text(value):
    return "" if value is None else _text(value)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate QFD JSON field")
        result[key] = value
    return result


def _time(value):
    if value in (None, ""):
        return None
    if not isinstance(value, str) or len(value) > 64:
        raise ValueError("Invalid QFD time")
    stamp = datetime.fromisoformat(value)
    if stamp.tzinfo is None or stamp.utcoffset() is None:
        raise ValueError("QFD time needs offset")
    return stamp.astimezone(UTC)


def _position(value, projected=False):
    if not isinstance(value, list) or len(value) not in (2, 3):
        raise ValueError("Invalid QFD position")
    if any(type(n) not in (int, float) or not math.isfinite(n) for n in value):
        raise ValueError("Invalid QFD ordinate")
    if projected:
        # EPSG:3857 inverse, WGS84 semi-major axis; see PROJ webmerc definition.
        radius = 6378137.0
        limit = math.pi * radius
        if abs(value[0]) > limit or abs(value[1]) > limit:
            raise ValueError("QFD Web Mercator position outside supported world bounds")
        value = [math.degrees(value[0] / radius),
                 math.degrees(math.atan(math.sinh(value[1] / radius))), *value[2:]]
    if not -180 <= value[0] <= 180 or not -90 <= value[1] <= 90:
        raise ValueError("QFD position outside geographic range")
    return tuple(value)  # Retain optional third ordinate; never infer its meaning.


def _geometry(value, kind, projected=False):
    if not isinstance(value, dict):
        raise ValueError("Missing QFD geometry")
    if kind == RecordKind.INCIDENT and value.get("type") == "Point":
        return OfficialGeometry(GeometryRole.INCIDENT_POINT, _position(value.get("coordinates"), projected))
    if kind != RecordKind.WARNING or value.get("type") != "Polygon":
        raise ValueError("Unsupported QFD geometry/record combination")
    rings = value.get("coordinates")
    if not isinstance(rings, list) or not rings or len(rings) > 100:
        raise ValueError("Invalid QFD polygon")
    if any(not isinstance(r, list) for r in rings) or sum(map(len, rings)) > MAX_VERTICES:
        raise ValueError("QFD polygon too large")
    result = []
    for ring in rings:
        points = tuple(_position(p, projected) for p in ring)
        if len(points) < 4 or points[0] != points[-1] or len(set(p[:2] for p in points)) < 3:
            raise ValueError("Invalid QFD ring")
        if len({len(p) for p in points}) != 1:
            raise ValueError("Inconsistent QFD ordinates")
        result.append(points)
    return OfficialGeometry(GeometryRole.WARNING_AREA, tuple(result))


def _record(feature, retrieved_at, projected=False):
    if not isinstance(feature, dict) or feature.get("type") != "Feature":
        raise ValueError("Invalid QFD feature")
    p = feature.get("properties")
    if not isinstance(p, dict):
        raise ValueError("Invalid QFD properties")
    event_type = _text(p.get("EventType"), required=True)
    fire_type = _text(p.get("GroupedType"), required=True)
    level = _text(p.get("WarningLevel"), required=True)
    if event_type != "Fire" or fire_type not in FIRE_TYPES:
        return None
    if level == "Information":
        kind = RecordKind.INCIDENT
    elif level in WARNING_LEVELS:
        kind = RecordKind.WARNING
    else:
        return None  # Unknown classification is counted, never mapped to no warning.
    source_id = p.get("UniqueID")
    if not isinstance(source_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", source_id):
        raise ValueError("Invalid QFD identity")
    return OfficialReport(
        provider="qld_qfd", source_id=source_id, kind=kind, jurisdiction="AU-QLD",
        title=_text(p.get("WarningTitle"), required=True), source_url=PUBLIC_URL,
        attribution=ATTRIBUTION, geometry=_geometry(feature.get("geometry"), kind, projected),
        raw_type=fire_type, raw_status=_optional_text(p.get("CurrentStatus")),
        raw_warning_level=level, planned_burn=fire_type == "FIRE PERMITTED BURN",
        retrieved_at=retrieved_at, event_updated_at=_time(p.get("ItemDateTimeLocal_ISO")),
        published_at=_time(p.get("PublishDateLocal_ISO")),
        expires_at=_time(p.get("ItemExpiryDateTimeLocal_ISO")),
        raw_updated=_optional_text(p.get("ItemDateTimeLocal_ISO")),
        agency="Queensland Fire Department", location=_optional_text(p.get("WarningArea")),
    )


def parse_feed(body: bytes, *, retrieved_at: datetime) -> ParsedReports:
    """Retain expired context explicitly; callers must not assume records are active."""
    if retrieved_at.tzinfo is None or retrieved_at.utcoffset() is None:
        raise ValueError("Receipt time needs timezone")
    if len(body) > MAX_BYTES:
        raise ValueError("QFD response too large")
    try:
        document = json.loads(body, object_pairs_hook=_unique_object)
    except (RecursionError, UnicodeError) as err:
        raise ValueError("Invalid QFD JSON") from err
    if not isinstance(document, dict) or document.get("type") != "FeatureCollection":
        raise ValueError("Invalid QFD collection")
    crs = document.get("crs")
    projected = crs == {"type": "name", "properties": {"name": "EPSG:3857"}}
    if crs is not None and not projected and crs != {
        "type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}
    }:
        raise ValueError("Unsupported QFD coordinate reference system")
    features = document.get("features")
    if not isinstance(features, list) or len(features) > MAX_ITEMS:
        raise ValueError("Invalid QFD feature count")
    groups = {}
    filtered = invalid = conflicts = 0
    for feature in features:
        try:
            record = _record(feature, retrieved_at, projected)
            if record is None:
                filtered += 1
            else:
                groups.setdefault(record.uid, []).append(record)
        except (ValueError, TypeError, KeyError, OverflowError):
            invalid += 1
    records = []
    minimum = datetime.min.replace(tzinfo=UTC)
    for group in groups.values():
        # Prefer an actual source revision, not a fresh feed publication timestamp.
        newest = max(r.event_updated_at or minimum for r in group)
        candidates = [r for r in group if (r.event_updated_at or minimum) == newest]
        # Only exact duplicates are safe to coalesce at an equal revision.
        if any(r != candidates[0] for r in candidates[1:]):
            conflicts += 1
        else:
            records.append(candidates[0])
    if features and invalid == len(features):
        raise ValueError("No readable QFD records")
    return ParsedReports(tuple(sorted(records, key=lambda r: r.uid)), len(features),
                         filtered, invalid, conflicts)
