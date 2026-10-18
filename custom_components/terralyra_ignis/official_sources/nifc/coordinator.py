"""Explicit NIFC request coordination; no scheduler or source activation."""
from __future__ import annotations

import asyncio
from dataclasses import replace
from .failure_details import failure_reason, validate_failure
from datetime import datetime, timezone
import math
import time

from .client import fetch_incidents_async
from .refresh import RefreshState, SourceHTTPError, due, failed, retry_after_seconds, succeeded, _clock


def checkpoint(state, *, now):
    """Export cooldown metadata only; no records or process-specific timestamps."""
    _clock(now)
    wait = max(0, state.next_attempt_at - now)
    data = dict(version=1, wait_seconds=None if math.isinf(wait) else math.ceil(wait),
                failures=state.failures)
    if math.isinf(wait) and state.resume_after_review_at is not None:
        _clock(state.resume_after_review_at)
        data.update(version=2, resume_wait_seconds=math.ceil(max(0, state.resume_after_review_at - now)))
    if state.failure_reason is not None:
        validate_failure(state.failure_reason, state.failure_http_status)
        return dict(version=3, cooldown=data, failure_reason=state.failure_reason,
                    http_status=state.failure_http_status)
    return data


def restore_checkpoint(data, *, now):
    """Restart the entire saved remaining wait, conservatively ignoring downtime.

    This avoids wall-clock jumps shortening a cooldown. Caller owns durable storage;
    a missing/corrupt checkpoint must not silently be treated as a fresh start.
    No saved response or user history is read, replaced or deleted here.
    """
    _clock(now)
    if isinstance(data, dict) and data.get('version') == 3:
        if type(data['version']) is not int or set(data) != {'version', 'cooldown', 'failure_reason', 'http_status'}:
            raise ValueError('Invalid diagnostic checkpoint')
        validate_failure(data['failure_reason'], data['http_status'])
        inner = data['cooldown']
        if not isinstance(inner, dict) or inner.get('version') not in (1, 2):
            raise ValueError('Invalid nested cooldown')
        state = restore_checkpoint(inner, now=now)
        return replace(state, failure_reason=data['failure_reason'],
                       failure_http_status=data['http_status'])
    keys = {'version','wait_seconds','failures'}
    if isinstance(data, dict) and data.get('version') == 2:
        keys.add('resume_wait_seconds')
    if not isinstance(data, dict) or set(data) != keys:
        raise ValueError('Invalid cooldown checkpoint')
    if type(data['version']) is not int or data['version'] not in (1, 2):
        raise ValueError('Unsupported cooldown version')
    count, wait = data['failures'], data['wait_seconds']
    if type(count) is not int or not 0 <= count <= 32:
        raise ValueError('Invalid failure count')
    if wait is not None and (type(wait) is not int or not 0 <= wait <= 10**12):
        raise ValueError('Invalid saved wait')
    resume = None
    if data['version'] == 2:
        seconds = data['resume_wait_seconds']
        if wait is not None or type(seconds) is not int or not 0 <= seconds <= 10**12:
            raise ValueError('Invalid recovery wait')
        resume = now + seconds
    return RefreshState(failures=count, next_attempt_at=math.inf if wait is None else now+wait,
                        status='restored_cooldown', resume_after_review_at=resume)


class NifcCoordinator:
    """Single-event-loop, single-instance request exclusion; explicit calls only."""
    def __init__(self, *, fetcher=fetch_incidents_async, state=None,
                 clock=time.monotonic, utcnow=lambda: datetime.now(timezone.utc)):
        self.state = state if state is not None else RefreshState()
        self._fetcher, self._clock, self._utcnow = fetcher, clock, utcnow
        self._lock = asyncio.Lock()

    async def refresh(self, *, enabled=False):
        # There is no await between the eligibility check and lock acquisition;
        # concurrent callers skip rather than queue an extra request.
        if not due(self.state, now=self._clock(), enabled=enabled, in_flight=self._lock.locked()):
            return 'skipped'
        async with self._lock:
            try:
                result = await self._fetcher()
                self.state = succeeded(self.state, result, now=self._clock(), received_at=self._utcnow())
            except asyncio.CancelledError:
                raise
            except SourceHTTPError as error:
                if error.status == 429:
                    kind = 'rate_limited'
                elif error.status in (408, 500, 502, 503, 504):
                    kind = 'transient'
                elif error.status in (401, 403):
                    kind = 'access_denied'
                else:
                    kind = 'invalid_data'
                self.state = failed(self.state, now=self._clock(), kind=kind,
                                    server_wait=retry_after_seconds(error.retry_after, now=self._utcnow()))
                self.state = replace(self.state, failure_reason='HTTP response rejected',
                                     failure_http_status=error.status)
                return 'failed'
            except (OSError, asyncio.TimeoutError) as error:
                self.state = failed(self.state, now=self._clock(), kind='transient')
                self.state = replace(self.state, failure_reason=('Request timed out'
                    if isinstance(error, TimeoutError) else 'Connection or response interrupted'),
                    failure_http_status=None)
                return 'failed'
            except ValueError as error:
                self.state = failed(self.state, now=self._clock(), kind='invalid_data')
                self.state = replace(self.state, failure_reason=failure_reason(error),
                                     failure_http_status=None)
                return 'failed'
            return 'retrieved'
