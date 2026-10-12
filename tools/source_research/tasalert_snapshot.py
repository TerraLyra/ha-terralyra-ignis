"""Offline comparison only; absence is not extinction and no records are deleted."""
from datetime import datetime
from tasalert_kml import parse_kml


def compare_snapshots(previous: bytes, current: bytes):
    """Validate both snapshots before producing a non-mutating change plan.

    Consumers must retain prior data on parse failure or review-required records.
    Identity reuse and source clock regressions require review, not replacement.
    """
    old = {r['id']: r for r in parse_kml(previous)}
    new = {r['id']: r for r in parse_kml(current)}
    changes = []
    for identifier in sorted(old.keys() | new.keys()):
        before, after = old.get(identifier), new.get(identifier)
        reasons = []
        if before is None:
            state = 'first_seen'
        elif after is None:
            state = 'not_in_snapshot'
        elif before == after:
            state = 'unchanged'
        else:
            # These are review signals, not proof of ID reuse.
            for field in ('feedType', 'number'):
                if before['fields'].get(field) != after['fields'].get(field):
                    reasons.append('identity_field_changed:' + field)
            for clock in ('created', 'changed'):
                a, b = before['record_times'].get(clock), after['record_times'].get(clock)
                if bool(a) != bool(b):
                    reasons.append('clock_availability_changed:' + clock)
                elif a and b:
                    first, second = datetime.fromisoformat(a), datetime.fromisoformat(b)
                    if clock == 'created' and first != second:
                        reasons.append('created_clock_changed')
                    elif clock == 'changed' and second < first:
                        reasons.append('changed_clock_regressed')
            if not reasons:
                a, b = before['record_times'].get('changed'), after['record_times'].get('changed')
                if not a or not b or datetime.fromisoformat(a) == datetime.fromisoformat(b):
                    reasons.append('content_changed_without_advancing_clock')
            state = 'review_required' if reasons else 'updated'
        changes.append({'id': identifier, 'state': state, 'reasons': reasons,
                        'previous': before, 'current': after})
    return {'changes': changes, 'empty_current_snapshot': not new,
            'deletes_records': False, 'infers_extinction': False}
