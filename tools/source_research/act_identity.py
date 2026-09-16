"""Offline identity and GeoRSS checks; no cross-snapshot stability claim."""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Optional
import re

from act_feed import ActItem

POINT = '{http://www.georss.org/georss}point'


@dataclass(frozen=True)
class IdentityLocation:
    identity_status: str
    source_id: Optional[str]
    location_status: str
    latitude: Optional[float]
    longitude: Optional[float]


def inspect_identity_location(item: ActItem) -> IdentityLocation:
    fields = dict(item.fields)
    if len(fields) != len(item.fields):
        raise ValueError('Duplicate raw fields')
    guid, cadid = fields.get('guid', '').strip(), fields.get('cadid', '').strip()
    source_id = None
    if not guid and not cadid:
        identity_status = 'missing'
    elif not guid or not cadid:
        identity_status = 'incomplete'
    elif guid != cadid:
        identity_status = 'conflict'
    else:
        identity_status, source_id = 'matching_pair', guid
    latitude = longitude = None
    raw = fields.get(POINT)
    if raw is None or not raw.strip():
        location_status = 'missing'
    else:
        location_status = 'invalid'
        parts = raw.split()
        if len(parts) == 2 and all(re.fullmatch(r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?', part) for part in parts):
            try:
                lat, lon = map(Decimal, parts)
                if (lat.is_finite() and lon.is_finite()
                        and Decimal(-90) <= lat <= Decimal(90)
                        and Decimal(-180) <= lon <= Decimal(180)):
                    latitude, longitude = float(lat), float(lon)
                    location_status = 'valid_point'
            except (InvalidOperation, ValueError):
                pass
    return IdentityLocation(identity_status, source_id, location_status, latitude, longitude)


def repeated_ids(items: tuple[ActItem, ...]) -> tuple[str, ...]:
    """Report repeated matching IDs without merging or picking a winning record."""
    seen, repeated = set(), set()
    for item in items:
        result = inspect_identity_location(item)
        if result.source_id is not None:
            if result.source_id in seen:
                repeated.add(result.source_id)
            seen.add(result.source_id)
    return tuple(sorted(repeated))
