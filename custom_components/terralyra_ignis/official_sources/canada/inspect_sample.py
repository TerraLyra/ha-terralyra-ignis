"""Offline CWFIF response checks. No network or Home Assistant interaction."""
import json
from datetime import datetime
from pathlib import Path


def inspect(payload):
    if payload.get('type') != 'FeatureCollection':
        raise ValueError('Expected FeatureCollection')
    features = payload.get('features')
    if not isinstance(features, list):
        raise ValueError('Missing feature list')
    matched = payload.get('numberMatched')
    returned = payload.get('numberReturned')
    issues = []
    if type(returned) is not int or returned != len(features):
        issues.append('returned_count_mismatch')
    complete = type(matched) is int and matched == len(features) and returned == len(features)
    identifiers = set()
    for index, feature in enumerate(features):
        props = feature.get('properties') or {}
        identity = props.get('national_fire_id')
        if not isinstance(identity, str) or not identity.strip():
            issues.append(f'{index}:missing_national_fire_id')
        elif identity in identifiers:
            issues.append(f'{index}:duplicate_national_fire_id')
        else:
            identifiers.add(identity)
        times = {}
        for field in ('situation_report_date', 'status_date', 'record_start', 'record_end'):
            value = props.get(field)
            if value is None:
                issues.append(f'{index}:{field}:missing')
                continue
            try:
                stamp = datetime.fromisoformat(value)
                if stamp.utcoffset() is None:
                    raise ValueError('No explicit offset')
                times[field] = stamp
            except (TypeError, ValueError):
                issues.append(f'{index}:{field}:invalid_or_naive')
        if 'record_start' in times and 'record_end' in times:
            if times['record_start'] >= times['record_end']:
                issues.append(f'{index}:invalid_validity_interval')
        contained = props.get('percent_contained')
        if contained == -1:
            issues.append(f'{index}:percent_contained:unknown_sentinel')
        elif contained is not None and (type(contained) not in (int, float) or not 0 <= contained <= 100):
            issues.append(f'{index}:percent_contained:invalid')
    return {'returned': len(features), 'matched': matched,
            'response_count_complete': complete, 'issues': issues,
            'national_coverage': 'not_established'}


if __name__ == '__main__':
    import sys
    print(json.dumps(inspect(json.loads(Path(sys.argv[1]).read_text())), indent=2))
