"""Shared experimental snapshot cache; caller-driven, no background/HA activation.

Use one instance per integration, not one per entity. Geometry is a previous-day
product; an hourly retrieval does not imply hourly geometry or fresh detections.
"""
import math
import random
import threading
import time
from inpe_centroids import STATES
from inpe_snapshot import collect_states


class RetryPending(RuntimeError):
    """A failed attempt is cooling down; old data must not look newly successful."""


class SnapshotCache:
    """Bounded one-scope cache with atomic replacement and single-flight access.

    First request is immediate. Subsequent attempts wait one hour plus 0–60s
    jitter, including after failure. No automatic retries or stale-success return.
    Scope changes are refused: create a new instance for an explicit reconfigure.
    The last successful snapshot is retained for separately labelled diagnostics.
    """

    def __init__(self, states, *, collect=collect_states, clock=time.monotonic,
                 jitter=lambda: random.uniform(0, 60)):
        if (not isinstance(states, (tuple, list)) or not 1 <= len(states) <= 3
                or any(not isinstance(s, str) or s not in STATES for s in states)
                or len(set(states)) != len(states)):
            raise ValueError('Expected one to three distinct state codes')
        self.states = tuple(sorted(states))
        self._collect = collect
        self._clock = clock
        self._jitter = jitter
        self._lock = threading.Lock()
        self.last_success = None
        self.last_error = None
        self.next_attempt = 0.0
        self._attempted = False

    def get(self):
        with self._lock:
            now = self._clock()
            if self._attempted and now < self.next_attempt:
                if self.last_error is not None:
                    raise RetryPending('Previous attempt failed; retry interval pending')
                return self.last_success
            offset = self._jitter()
            if (type(offset) not in (int, float) or not math.isfinite(offset)
                    or not 0 <= offset <= 60):
                raise ValueError('Jitter must be between zero and sixty seconds')
            self._attempted = True
            try:
                snapshot = self._collect(self.states)
            except Exception as exc:
                self.last_error = type(exc).__name__
                raise
            else:
                self.last_success = snapshot
                self.last_error = None
                return snapshot
            finally:
                self.next_attempt = self._clock() + 3600 + offset
