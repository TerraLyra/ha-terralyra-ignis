"""Experimental state inventories; no HA polling, disk writes or event closure."""
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
import time
from inpe_centroids import STATES, Centroid
from inpe_fetch import fetch_centroids
from inpe_events import ATTRIBUTION, LICENSE_URL


@dataclass(frozen=True)
class Snapshot:
    requested_states: tuple[str, ...]
    records: tuple[Centroid, ...]
    retrieved_at: datetime
    complete: bool = False  # Valid schema is not evidence of upstream completeness.
    production_ready: bool = False


def collect_states(states, *, fetch=fetch_centroids, sleep=time.sleep,
                   now=lambda: datetime.now(timezone.utc)):
    """At most three states (24 MiB payload cap), sequential with 1s spacing.

    Duplicate identical records across states are retained once. Conflicts abort
    the entire cycle, which may have crossed an upstream publication boundary.
    Never return a partial inventory after a failed state request. Three states
    is a research resource limit, not a provider quota or geographical coverage.
    """
    if (not isinstance(states, (tuple, list)) or not 1 <= len(states) <= 3
            or any(not isinstance(s, str) or s not in STATES for s in states)
            or len(set(states)) != len(states)):
        raise ValueError('Expected one to three distinct state codes')
    selected = tuple(sorted(states))
    start = now()
    if start.tzinfo is None or start.utcoffset() != timedelta(0):
        raise ValueError('UTC retrieval clock required')
    records = {}
    for index, state in enumerate(selected):
        if index:
            sleep(1)
        batch = fetch(state=state)
        if not batch:
            raise ValueError('Empty inventory semantics unverified')
        seen = set()
        for record in batch:
            if not isinstance(record, Centroid) or state not in record.states or record.source_id in seen:
                raise ValueError('Invalid state response')
            seen.add(record.source_id)
            previous = records.get(record.source_id)
            if previous is not None and previous != record:
                raise ValueError('Conflicting cross-state event')
            records[record.source_id] = record
    end = now()
    if end.tzinfo is None or end.utcoffset() != timedelta(0) or end < start:
        raise ValueError('Invalid retrieval clock')
    return Snapshot(selected, tuple(records[k] for k in sorted(records)), end)


def report(snapshot):
    """Plain data for a future view, no HTML or calendar/observation timestamps."""
    return {
        'attribution': ATTRIBUTION,
        'source_url': 'https://data.inpe.br/queimadas/portal/evento-fogo/',
        'license_url': LICENSE_URL,
        'modifications': 'State selection, field selection and cross-state deduplication.',
        'provisional': True,
        'coverage': 'requested_states_only',
        'requested_states': snapshot.requested_states,
        'retrieved_at': snapshot.retrieved_at.isoformat(),
        'observation_time_known': False,
        'complete': False,
        'production_ready': False,
        'events': [dict(source_id=r.source_id, category=r.category, status=r.status,
                        estimated_area_ha=r.area_ha, duration_days=r.duration_days,
                        municipality=r.municipality, states=r.states,
                        representative_longitude=r.longitude,
                        representative_latitude=r.latitude) for r in snapshot.records],
    }
