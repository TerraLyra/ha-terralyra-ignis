"""Source-age and complex relationship diagnostics, never fire activity evidence."""
from datetime import datetime, timedelta

from .records import IncidentRecord


def source_age(record: IncidentRecord, *, now: datetime, max_age: timedelta) -> str:
    """Caller explicitly chooses a display-age threshold; receipt time is not used.

    Record modification age does not establish observation age or fire closure.
    """
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError('Timezone-aware assessment time required')
    if not isinstance(max_age, timedelta) or max_age <= timedelta(0):
        raise ValueError('Positive source-age threshold required')
    modified = record.modified_at
    if modified is None:
        return 'unknown'
    if modified.tzinfo is None or modified.utcoffset() is None:
        raise ValueError('Timezone-aware source modification required')
    if modified > now:
        return 'future_source_time'
    return 'within_threshold' if now - modified <= max_age else 'older_than_threshold'


def complex_roles(records: tuple[IncidentRecord, ...]) -> tuple[str, ...]:
    """Preserve every record and classify links; never sum complexes with children.

    Missing parent in a supplied result is unresolved, not proof of independent fire.
    No geographic/name matching, merging or deletion is performed.
    """
    by_id = {record.irwin_id: record for record in records}
    if len(by_id) != len(records):
        raise ValueError('Duplicate incident identity')
    roles = []
    for record in records:
        if record.category == 'incident_complex':
            role = 'complex_relationship_unresolved' if record.complex_child or record.parent_complex_id else 'complex_container'
        elif record.complex_child is False and record.parent_complex_id is None:
            role = 'reported_non_child'
        elif record.complex_child is True and record.parent_complex_id:
            parent = by_id.get(record.parent_complex_id)
            if parent is None:
                role = 'parent_not_in_result'
            elif parent.category != 'incident_complex' or parent.complex_child or parent.parent_complex_id:
                role = 'parent_relationship_conflict'
            else:
                role = 'linked_complex_member'
        else:
            role = 'relationship_unknown'
        roles.append(role)
    return tuple(roles)
