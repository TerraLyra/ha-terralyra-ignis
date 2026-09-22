"""Local NIFC report projection, without correlation or incident-history changes."""
from dataclasses import dataclass

from .core.geo import haversine_km
from .core.locations import validate_monitored_locations
from .official_sources.nifc.assessment import complex_roles
from .official_sources.nifc.records import IncidentRecord

SOURCE_URL = 'https://www.arcgis.com/home/item.html?id=4181a117dc9e43db8598533e29972015'
ATTRIBUTION = 'NIFC / WFIGS / IRWIN'
LABELS = {
    'en': {'wildfire': 'Wildfire report', 'prescribed_fire': 'Prescribed-fire report',
           'incident_complex': 'Incident-complex report', 'modified': 'Record updated',
           'discovered': 'Discovery reported'},
    'hu': {'wildfire': 'Erdőtűzjelentés', 'prescribed_fire': 'Tervezett égetés jelentése',
           'incident_complex': 'Tűzkomplexum jelentése', 'modified': 'Adatlap frissítése',
           'discovered': 'Jelentett felfedezés'},
}


@dataclass(frozen=True)
class NifcLocationMatch:
    id: str
    name: str
    distance_km: float


@dataclass(frozen=True)
class NifcPresentedRecord:
    record: IncidentRecord
    matches: tuple[NifcLocationMatch, ...]
    complex_role: str


def project_nifc(result, locations):
    """Match only enabled circles; no Home fallback or inferred complex geometry."""
    locations = tuple(locations)
    validate_monitored_locations(locations)
    if result is None:
        return ()
    if result.outcome != 'terminal_reported' or len(result.records) > 10000:
        raise ValueError('Validated bounded response required')
    presented = []
    for record, role in zip(result.records, complex_roles(result.records)):
        if record.latitude is None or record.longitude is None:
            continue
        matches = []
        for location in locations:
            if not location.enabled:
                continue
            distance = haversine_km(location.latitude, location.longitude,
                                    record.latitude, record.longitude)
            if distance <= location.radius_km:
                matches.append(NifcLocationMatch(location.id, location.name, distance))
        if matches:
            presented.append(NifcPresentedRecord(record,
                tuple(sorted(matches, key=lambda m: (m.distance_km, m.id))), role))
    return tuple(presented)


def record_title(item, language='en'):
    labels = LABELS.get(language, LABELS['en'])
    return f"NIFC · {labels[item.record.category]} · {item.record.irwin_id[:8]}"


def record_attributes(item):
    record = item.record
    return {'irwin_id': record.irwin_id, 'report_category': record.category,
            'source_url': SOURCE_URL, 'attribution': ATTRIBUTION,
            'incident_name': record.incident_name, 'incident_text': record.incident_text,
            'incident_text_status': record.incident_text_status,
            'source_modified_at': record.modified_at.isoformat() if record.modified_at else None,
            'source_discovered_at': record.discovered_at.isoformat() if record.discovered_at else None,
            'complex_role': item.complex_role, 'parent_complex_id': record.parent_complex_id,
            'location_matches': [{'location_id': m.id, 'location_name': m.name,
                                  'distance_km': round(m.distance_km, 3)} for m in item.matches],
            'distance_reference_id': item.matches[0].id,
            'distance_reference_name': item.matches[0].name,
            'source_freshness': 'not_established', 'active_fire_status': 'not_established'}
