"""Aggregate offline inspection; intentionally excludes raw event details."""
from collections import Counter
from act_feed import inspect_feed
from act_classification import classify_item
from act_identity import inspect_identity_location
from act_times import inspect_times


def summarize_feed(payload: bytes, *, max_bytes=1_048_576, max_items=10_000) -> dict:
    """Inspect the entire bounded feed or raise; never return partial success.

    Counts overlap across dimensions. No event is declared operationally usable.
    Output contains fixed labels and counts only, not IDs, locations or raw text.
    """
    items = inspect_feed(payload, max_bytes=max_bytes, max_items=max_items)
    categories, exercises, identities, locations = (Counter() for _ in range(4))
    times = {key: Counter() for key in ('publication', 'updated', 'call')}
    ids = Counter()
    for item in items:
        classification = classify_item(item)
        identity = inspect_identity_location(item)
        timing = inspect_times(item)
        categories[classification.category.value] += 1
        exercises[classification.exercise_evidence.value] += 1
        identities[identity.identity_status] += 1
        locations[identity.location_status] += 1
        if identity.source_id is not None:
            ids[identity.source_id] += 1
        for key, counts in times.items():
            counts[getattr(timing, key).status] += 1
    def ordered(counts):
        return dict(sorted(counts.items()))
    return {
        'schema_version': 1,
        'purpose': 'offline_source_research',
        'production_readiness': 'not_established',
        'record_count': len(items),
        'categories': ordered(categories),
        'exercise_evidence': ordered(exercises),
        'identity': ordered(identities),
        'location': ordered(locations),
        'times': {key: ordered(counts) for key, counts in times.items()},
        'repeated_matching_id_groups': sum(count > 1 for count in ids.values()),
        'records_in_repeated_matching_id_groups': sum(count for count in ids.values() if count > 1),
    }
