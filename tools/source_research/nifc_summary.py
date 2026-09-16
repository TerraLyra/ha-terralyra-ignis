"""Aggregate display preparation; source-record counts, never active-fire totals."""
from datetime import datetime, timedelta

from nifc_assessment import complex_roles, source_age
from nifc_refresh import RefreshState, _clock

CATEGORIES = ('wildfire', 'prescribed_fire', 'incident_complex')
AGES = ('unknown', 'future_source_time', 'within_threshold', 'older_than_threshold')
ROLES = ('complex_container', 'complex_relationship_unresolved', 'reported_non_child',
         'parent_not_in_result', 'parent_relationship_conflict', 'linked_complex_member',
         'relationship_unknown')


def summarize(state: RefreshState, *, now: datetime, monotonic_now: float,
              max_source_age: timedelta, max_retrieval_age: timedelta) -> dict:
    """Summarize a normalized cache without raw IDs, coordinates or source dates.

    Both thresholds are explicit display policy inputs. Cache age and source-record
    modification age are independent. A failed refresh never makes retained data
    current, and a terminal pagination response is not national completeness.
    """
    _clock(monotonic_now)
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError('Aware display time required')
    for threshold in (max_source_age, max_retrieval_age):
        if not isinstance(threshold, timedelta) or threshold <= timedelta(0):
            raise ValueError('Positive display thresholds required')
    if state.last_success is None:
        return {'schema_version': 1, 'availability': 'no_cached_response',
                'source_record_count': None, 'national_completeness': 'not_established',
                'active_fire_count': None}
    result = state.last_success
    if result.outcome != 'terminal_reported':
        raise ValueError('Partial response is not a successful cache')
    records = result.records
    if not isinstance(records, tuple) or len(records) > 10000:
        raise ValueError('Expected bounded normalized records')
    roles = complex_roles(records)
    categories = {key: 0 for key in CATEGORIES}
    ages = {key: 0 for key in AGES}
    relationships = {key: 0 for key in ROLES}
    missing_location = missing_discovery = 0
    for record, role in zip(records, roles):
        if record.category not in categories:
            raise ValueError('Unexpected normalized category')
        categories[record.category] += 1
        ages[source_age(record, now=now, max_age=max_source_age)] += 1
        relationships[role] += 1
        missing_location += record.latitude is None or record.longitude is None
        missing_discovery += record.discovered_at is None
    if state.last_success_at is None:
        retrieval = 'unknown'
    else:
        _clock(state.last_success_at)
        elapsed = monotonic_now - state.last_success_at
        if elapsed < 0:
            retrieval = 'clock_mismatch'
        else:
            retrieval = 'within_threshold' if elapsed <= max_retrieval_age.total_seconds() else 'older_than_threshold'
    return {
        'schema_version': 1,
        'availability': 'cached_response' if state.status == 'retrieved' else 'retained_response',
        'retrieval_age': retrieval,
        'source_record_count': len(records),
        'records_by_category': categories,
        'records_by_modification_age': ages,
        'records_by_complex_role': relationships,
        'missing_location_count': missing_location,
        'missing_discovery_time_count': missing_discovery,
        'source_age_threshold_seconds': max_source_age.total_seconds(),
        'retrieval_age_threshold_seconds': max_retrieval_age.total_seconds(),
        'national_completeness': 'not_established',
        'active_fire_count': None,
    }
