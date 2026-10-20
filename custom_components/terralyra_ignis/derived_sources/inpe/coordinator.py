"""Shared async collection owner, ready for HA consumers; opt-in wiring pending."""
import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
import random
import time
from .centroids import STATES
from .client import fetch_state


@dataclass(frozen=True)
class State:
    response_status: str = 'not_requested'
    records: tuple = ()
    last_success: datetime | None = None
    error: str | None = None
    complete: bool = False


class Coordinator:
    """Atomic returned inventory; no historical deletion or fire-state inference.

    One instance per explicit state selection, shared across HA consumers. Uses
    the caller-owned session; no close/restart of HA resources. Old data survives
    errors but response_status makes it unavailable for fresh-success consumers.
    """
    def __init__(self, session, states, *, fetch=fetch_state, monotonic=time.monotonic,
                 now=lambda: datetime.now(timezone.utc), jitter=lambda: random.uniform(0,60)):
        if (not isinstance(states,(tuple,list)) or not 1<=len(states)<=3
                or any(not isinstance(s,str) or s not in STATES for s in states)
                or len(set(states))!=len(states)):
            raise ValueError('Expected one to three distinct states')
        self.states=tuple(sorted(states))
        self.session=session
        self.fetch=fetch
        self.monotonic=monotonic
        self.now=now
        self.jitter=jitter
        self.state=State()
        self._next=None
        self._lock=asyncio.Lock()

    async def async_refresh(self):
        async with self._lock:
            if self._next is not None and self.monotonic()<self._next:
                return self.state
            offset=self.jitter()
            if type(offset) not in (int,float) or not 0<=offset<=60:
                raise ValueError('Invalid jitter')
            # Reserve eligibility before network I/O; even cancellation cannot
            # trigger a tight request loop during reload/shutdown.
            self._next=self.monotonic()+3600+offset
            try:
                records={}
                for state in self.states:
                    for record in await self.fetch(self.session,state):
                        if state not in record.states:
                            raise ValueError('state_mismatch')
                        previous=records.get(record.source_id)
                        if previous is not None and previous!=record:
                            raise ValueError('conflicting_records')
                        records[record.source_id]=record
                receipt=self.now()
                if receipt.tzinfo is None or receipt.utcoffset().total_seconds()!=0:
                    raise ValueError('Invalid UTC clock')
                self.state=State('success',tuple(records[k] for k in sorted(records)),receipt)
            except asyncio.CancelledError:
                raise
            except Exception:
                self.state=State('error',self.state.records,self.state.last_success,'retrieval_failed')
            finally:
                self._next=self.monotonic()+3600+offset
            return self.state
