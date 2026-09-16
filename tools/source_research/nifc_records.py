"""Offline NIFC record normalization; no retrieval, alerts or history writes."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import math
import re
from uuid import UUID

from nifc_page import inspect_page


@dataclass(frozen=True)
class IncidentRecord:
    irwin_id: str
    category: str
    longitude: float | None
    latitude: float | None
    discovered_at: datetime | None
    modified_at: datetime | None
    complex_child: bool | None = None
    parent_complex_id: str | None = None


def _identity(value):
    if not isinstance(value, str):
        raise ValueError('Missing IRWIN identity')
    value = value.strip()
    if value.startswith('{') and value.endswith('}'):
        value = value[1:-1]
    if not re.fullmatch(r'[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}', value):
        raise ValueError('Invalid IRWIN identity')
    identity = UUID(value)
    if identity.int == 0:
        raise ValueError('Nil IRWIN identity')
    return str(identity)


def _time(value):
    if value is None:
        return None
    if type(value) is not int:
        raise ValueError('Expected UTC epoch milliseconds')
    try:
        return datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(milliseconds=value)
    except OverflowError as error:
        raise ValueError('Date outside supported range') from error


def _point(geometry):
    if geometry is None:
        return None, None
    if not isinstance(geometry, dict):
        raise ValueError('Invalid point')
    # Per-feature CRS overrides are outside this deliberately narrow query contract.
    if 'spatialReference' in geometry:
        raise ValueError('Unexpected per-feature spatial reference')
    x, y = geometry.get('x'), geometry.get('y')
    for value, bound in ((x, 180), (y, 90)):
        if type(value) not in (int, float) or not -bound <= value <= bound or not math.isfinite(value):
            raise ValueError('Invalid WGS84 coordinate')
    return float(x), float(y)


def normalize_page(page: dict, *, max_records: int = 2000) -> tuple[IncidentRecord, ...]:
    """Normalize a bounded decoded page after envelope checks.

    A missing/null source date or geometry stays missing. Unknown categories fail
    closed. No clock fallback, location fallback, inferred ignition or closure.
    The caller must separately inspect continuation; this tuple is never a claim
    of completeness. Duplicate IRWIN IDs reject the page rather than merging it.
    """
    inspect_page(page, max_records=max_records)
    records, identities = [], set()
    categories = {'WF': 'wildfire', 'RX': 'prescribed_fire', 'CX': 'incident_complex'}
    for feature in page['features']:
        attributes = feature['attributes']
        identity = _identity(attributes.get('IrwinID'))
        if identity in identities:
            raise ValueError('Repeated IRWIN identity')
        identities.add(identity)
        category = attributes.get('IncidentTypeCategory')
        if not isinstance(category, str) or category not in categories:
            raise ValueError('Unknown incident category')
        child = attributes.get('IsCpxChild')
        if child is not None and (type(child) is not int or child not in (0, 1)):
            raise ValueError('Invalid complex-child flag')
        parent = attributes.get('CpxID')
        parent = None if parent is None or parent == '' else _identity(parent)
        if parent == identity or (child == 0 and parent is not None):
            raise ValueError('Conflicting complex relationship')
        longitude, latitude = _point(feature.get('geometry'))
        records.append(IncidentRecord(
            identity, categories[category], longitude, latitude,
            _time(attributes.get('FireDiscoveryDateTime')),
            _time(attributes.get('ModifiedOnDateTime_dt')),
            None if child is None else bool(child), parent,
        ))
    return tuple(records)
