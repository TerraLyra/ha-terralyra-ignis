"""Offline Victoria type/point inspection; not an operational fire classifier."""
from collections import Counter
from dataclasses import dataclass
import math
from typing import Optional


@dataclass(frozen=True)
class RecordEvidence:
    upstream: tuple
    category: str
    location_status: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None


def inspect_record(record: dict) -> RecordEvidence:
    """Retain raw fields; exact source pairs only, without free-text inference.

    A valid point establishes global numeric validity only, not jurisdiction,
    positional accuracy, fire extent or relevance to a monitored location.
    """
    category, subtype = record.get('category1'), record.get('category2')
    if category == 'Fire':
        label = {'Bushfire':'vegetation_fire_candidate', 'Building':'structure_fire',
                 'False Alarm':'reported_false_alarm'}.get(subtype, 'fire_unspecified')
    else:
        label = {'Accident / Rescue':'accident_rescue', 'Medical':'medical',
                 'Other':'other'}.get(category, 'unknown')
    raw_lat, raw_lon = record.get('latitude'), record.get('longitude')
    lat = lon = None
    if raw_lat is None and raw_lon is None:
        status = 'missing'
    elif raw_lat is None or raw_lon is None:
        status = 'incomplete'
    elif type(raw_lat) not in (int,float) or type(raw_lon) not in (int,float):
        status = 'invalid'
    else:
        try:
            if (math.isfinite(raw_lat) and math.isfinite(raw_lon)
                    and -90 <= raw_lat <= 90 and -180 <= raw_lon <= 180):
                lat,lon=float(raw_lat),float(raw_lon)
                status='valid_point'
            else:
                status='invalid'
        except OverflowError:
            status='invalid'
    return RecordEvidence(tuple(record.items()),label,status,lat,lon)


def summarize_spatial(records):
    """Fixed diagnostic keys, never raw categories, text or coordinates."""
    categories,locations=Counter(),Counter()
    for record in records:
        evidence=inspect_record(record)
        categories[evidence.category]+=1
        locations[evidence.location_status]+=1
    return {'status':'experimental','production_readiness':'not_established',
            'record_count':len(records),'categories':dict(sorted(categories.items())),
            'locations':dict(sorted(locations.items()))}
