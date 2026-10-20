"""INPE centroid presentation, separate from detections and official warnings."""
import math


def project_inpe(state, locations):
    """Show current successful inventory within enabled monitoring circles only."""
    if state is None or state.response_status != 'success':
        return ()
    rows = []
    for record in state.records:
        matches = []
        for location in locations:
            if not location.enabled:
                continue
            p1, p2 = math.radians(location.latitude), math.radians(record.latitude)
            a = math.sin((p2-p1)/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(math.radians(record.longitude-location.longitude)/2)**2
            distance = 6371.0088 * 2 * math.asin(math.sqrt(min(1, max(0, a))))
            if distance <= location.radius_km:
                matches.append((distance, location.id, location.name))
        if matches:
            distance, location_id, name = min(matches)
            rows.append(dict(record=record, distance_km=distance, location_id=location_id,
                             location_name=name, latitude=record.latitude, longitude=record.longitude,
                             category=record.category))
    return tuple(rows)


def record_key(item):
    return str(item['record'].source_id)


def record_title(item, language):
    return f"{item['record'].municipality} · INPE {item['record'].source_id}"


def record_attributes(item):
    record = item['record']
    return {
        'source_id': record.source_id,
        'source_status': record.status,
        'report_category': record.category,
        'distance_reference_name': item['location_name'],
        'distance_reference_id': item['location_id'],
        'estimated_area_ha': record.area_ha,
        'requested_record_states': list(record.states),
        'provisional': True,
        'coverage_complete': False,
        'geometry_update_basis': 'previous_day',
        'position_meaning': 'representative_centroid_not_fire_perimeter',
        'incident_text_status': 'not_in_feed',
        'attribution': 'INPE / Programa Queimadas',
        'license_url': 'https://creativecommons.org/licenses/by-sa/4.0/',
        'source_url': 'https://data.inpe.br/queimadas/portal/evento-fogo/',
        'transformation': 'State and centroid-distance filtering, field selection and cross-state deduplication.',
    }
