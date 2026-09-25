"""Bounded offline JCyL response review. No HA, network or incident promotion."""
import argparse
from copy import deepcopy
from datetime import date, time
import json
import math
from pathlib import Path

MAX_BYTES = 1024 * 1024
MAX_ROWS = 100


def repeated_point_evidence(rows):
    """Flag shared points across differing onset values, never merge incidents."""
    groups = {}
    for index, row in enumerate(rows):
        point = row.get('posicion')
        onset = (row.get('fecha_de_inicio'), row.get('hora_de_inicio'))
        if not isinstance(point, dict) or not all(isinstance(v, str) and v for v in onset):
            continue
        lat, lon = point.get('lat'), point.get('lon')
        if not all(type(v) in (int, float) and math.isfinite(v) for v in (lat, lon)):
            continue
        if abs(lat) > 90 or abs(lon) > 180:
            continue
        groups.setdefault((lat, lon), []).append((index, onset))
    return [dict(row_indexes=[i for i, _ in values],
                 distinct_onset_values=len({o for _, o in values}),
                 interpretation='shared_point_requires_review')
            for values in groups.values() if len({o for _, o in values}) > 1]


def inspect_response(raw):
    if len(raw) > MAX_BYTES:
        raise ValueError('Response exceeds 1 MiB')
    payload = json.loads(raw)
    if not isinstance(payload, dict) or not isinstance(payload.get('results'), list):
        raise ValueError('Expected API results array')
    rows = payload['results']
    if len(rows) > MAX_ROWS or any(not isinstance(r, dict) for r in rows):
        raise ValueError('Expected at most 100 record objects')
    collected = 'snapshot_verified' in payload or 'count_complete' in payload
    total = payload.get('total_count')
    if collected and total is None and not rows:
        total = 0  # Empty failed collection: completeness remains false below.
    if type(total) is not int or total < len(rows):
        raise ValueError('Invalid total_count')
    reviewed = []
    for row in rows:
        issues = []
        town = row.get('termino_municipal')
        no_incident = isinstance(town, str) and town.strip().upper() == 'SIN INCIDENCIAS'
        if not isinstance(town, str) or not town.strip():
            issues.append('missing_locality')
        # Validate syntax only; timezone and DST interpretation are not inferred.
        for field in ('fecha_del_parte', 'fecha_de_inicio', 'fecha_extinguido'):
            value = row.get(field)
            if value is not None:
                try:
                    if not isinstance(value, str) or len(value) != 10:
                        raise ValueError()
                    date.fromisoformat(value)
                except ValueError:
                    issues.append('invalid_' + field)
        for field in ('hora_del_parte', 'hora_de_inicio', 'hora_extinguido'):
            value = row.get(field)
            if value is not None:
                try:
                    if not isinstance(value, str) or len(value) != 5:
                        raise ValueError()
                    time.fromisoformat(value)
                except ValueError:
                    issues.append('invalid_' + field)
        for prefix in ('parte', 'inicio', 'extinguido'):
            d, t = {'parte': ('fecha_del_parte', 'hora_del_parte'),
                    'inicio': ('fecha_de_inicio', 'hora_de_inicio'),
                    'extinguido': ('fecha_extinguido', 'hora_extinguido')}[prefix]
            if (row.get(d) is None) != (row.get(t) is None):
                issues.append('incomplete_' + prefix + '_time')
        if row.get('fecha_del_parte') is None:
            issues.append('missing_report_date')
        status = row.get('situacion_actual')
        normalized = status.strip().upper() if isinstance(status, str) else None
        if row.get('fecha_extinguido') is not None and normalized != 'EXTINGUIDO':
            issues.append('extinction_time_status_conflict')
        if no_incident and any(row.get(k) is not None for k in ('fecha_de_inicio', 'situacion_actual', 'posicion')):
            issues.append('no_incident_row_has_incident_fields')
        point = row.get('posicion')
        if point is not None:
            valid = isinstance(point, dict) and all(
                type(point.get(k)) in (int, float) and math.isfinite(point[k]) and abs(point[k]) <= limit
                for k, limit in (('lat', 90), ('lon', 180)))
            issues.append('geometry_semantics_unverified' if valid else 'invalid_geometry')
        reviewed.append(dict(source=deepcopy(row), record_kind='no_incident_notice' if no_incident else 'report_candidate',
                             issues=issues, incident_id_verified=False,
                             incident_location_verified=False, timestamp_semantics_verified=False))
    return dict(schema_version=1, total_count=total, inspected_rows=len(rows),
                response_complete=(len(rows) == total and not collected),
                collection_status=({k: payload.get(k) for k in ('count_complete', 'snapshot_verified', 'reason', 'pages_received')} if collected else None),
                national_coverage=False,
                shared_point_evidence=repeated_point_evidence(rows),
                results=reviewed)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('sample', type=Path)
    args = parser.parse_args()
    with args.sample.open('rb') as stream:
        result = inspect_response(stream.read(MAX_BYTES + 1))
    print(json.dumps(result, ensure_ascii=False, indent=2))
