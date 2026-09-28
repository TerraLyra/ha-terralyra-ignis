"""Compare two saved homepage samples; no lifecycle or incident-ID inference."""
from collections import defaultdict
from fr_alert_listing import inspect_listing
from fr_alert_review import value


def compare_samples(before, after):
    snapshots = [inspect_listing(raw) for raw in (before, after)]
    groups = []
    unidentified = []
    for snapshot in snapshots:
        indexed = defaultdict(list)
        missing = []
        for index, item in enumerate(snapshot['results']):
            source = item['source']
            identifier = value(source, 'identifier')
            if isinstance(identifier, str) and identifier.strip():
                indexed[identifier].append(source)
            else:
                missing.append(index)
        groups.append(indexed)
        unidentified.append(missing)
    old, new = groups
    changes = []
    for identifier in sorted(old.keys() | new.keys()):
        left, right = old.get(identifier, []), new.get(identifier, [])
        if len(left) > 1 or len(right) > 1:
            kind = 'ambiguous_duplicate'
        elif not left:
            kind = 'newly_observed'
        elif not right:
            kind = 'not_observed_in_second_sample'
        elif left == right:
            kind = 'unchanged'
        else:
            kind = 'source_changed'
        changes.append(dict(identifier=identifier, kind=kind, before=left, after=right))
    return dict(changes=changes, unidentified_row_indexes=unidentified,
                lifecycle_verified=False, snapshot_complete=False)
