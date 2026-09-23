"""Pure research refresh decisions; no timers, requests or persistent history."""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import math
import re

from .query import FetchResult


from .errors import SourceHTTPError


def retry_after_seconds(value, *, now: datetime):
    """Return a server minimum wait; malformed values fall back to local policy.

    Excessively large valid numeric delays return infinity (manual review), never
    a shortened wait. HTTP dates require a timezone; now must be timezone-aware.
    """
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError('Aware response receipt time required')
    if not isinstance(value, str):
        return None
    value = value.strip()
    if re.fullmatch(r'[0-9]+', value):
        if len(value) > 12:
            return math.inf
        return int(value)
    if len(value) > 128:
        return None
    try:
        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            return None
        return max(0, math.ceil((parsed - now.astimezone(timezone.utc)).total_seconds()))
    except (ValueError, TypeError, OverflowError):
        return None


@dataclass(frozen=True)
class RefreshState:
    last_success: FetchResult | None = None
    last_success_at: float | None = None
    failures: int = 0
    next_attempt_at: float = 0
    status: str = 'never_fetched'
    resume_after_review_at: float | None = None
    received_at: datetime | None = None


def _clock(value):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ValueError('Finite nonnegative monotonic time required')


def due(state: RefreshState, *, now: float, enabled: bool, in_flight: bool) -> bool:
    _clock(now)
    if type(enabled) is not bool or type(in_flight) is not bool:
        raise ValueError('Explicit boolean enablement and in-flight state required')
    return enabled and not in_flight and now >= state.next_attempt_at


def succeeded(state: RefreshState, result: FetchResult, *, now: float, received_at: datetime | None = None) -> RefreshState:
    _clock(now)
    if not isinstance(result, FetchResult) or result.outcome != 'terminal_reported':
        raise ValueError('Only validated terminal retrieval may update the snapshot')
    # Latest response cache only, never the incident history or proof of freshness.
    if received_at is not None:
        if not isinstance(received_at, datetime) or received_at.tzinfo is None or received_at.utcoffset() is None:
            raise ValueError('Aware receipt timestamp required')
        received_at = received_at.astimezone(timezone.utc)
    return RefreshState(result, now, 0, now + 900, 'retrieved', received_at=received_at)


def failed(state: RefreshState, *, now: float, kind: str,
           server_wait: float | None = None) -> RefreshState:
    _clock(now)
    if kind not in ('transient', 'rate_limited', 'invalid_data', 'access_denied'):
        raise ValueError('Unknown failure classification')
    if server_wait is not None and (type(server_wait) not in (int, float)
                                   or math.isnan(server_wait) or server_wait < 0):
        raise ValueError('Invalid server wait')
    failures = min(state.failures + 1, 32)
    delay = min(900 * 2 ** min(failures - 1, 5), 21600)
    if kind in ('invalid_data', 'access_denied'):
        delay = math.inf
    if server_wait is not None:
        delay = max(delay, server_wait)
    resume = None
    if kind in ('invalid_data', 'access_denied') and not math.isinf(server_wait or 0):
        resume = max(state.next_attempt_at, now + max(900, server_wait or 0))
    return replace(state, failures=failures, next_attempt_at=max(state.next_attempt_at, now + delay),
                   status='refresh_failed_' + kind, resume_after_review_at=resume)
