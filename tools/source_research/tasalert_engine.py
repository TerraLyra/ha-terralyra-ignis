"""Offline composition of response policy and retained records; no network I/O."""
from copy import deepcopy
from dataclasses import dataclass, field, replace
from tasalert_policy import State, apply_response
from tasalert_retention import reconcile


@dataclass(frozen=True)
class Engine:
    response: State = field(default_factory=State)
    ledger: dict = field(default_factory=dict)
    review: tuple = ()
    expired: tuple = ()


def advance(engine, now, status, body=b'', etag=None, retry_after=None):
    """Return a new engine atomically; the caller keeps old state on exceptions.

    Response snapshot is the latest validated representation; ledger entries may
    retain earlier payloads requiring review. A 304 never refreshes last_seen or
    expires records. It preserves review diagnostics from the accepted snapshot.
    """
    old = engine.response
    # Snapshot-level missing/conflict holds are replaced with per-record decisions.
    candidate = apply_response(replace(old, snapshot=None, etag=None) if status == 200 else old,
                               now, status, body, etag, retry_after)
    if status != 200 or candidate.status != 'accepted':
        if status != 304 or candidate.status != 'not_modified':
            candidate = replace(candidate, snapshot=old.snapshot, etag=old.etag)
        return Engine(candidate, deepcopy(engine.ledger), engine.review, ())
    try:
        result = reconcile(engine.ledger, body, now)
    except ValueError:
        # Preserve both layers on a ledger/capacity error and use failure backoff.
        failed = apply_response(old, now, 503, retry_after=retry_after)
        return Engine(replace(failed,status='replacement_review'),deepcopy(engine.ledger),engine.review,())
    return Engine(candidate,result['records'],tuple(result['review']),tuple(result['expired']))
