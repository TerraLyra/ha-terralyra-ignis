"""Shared opt-in scheduler; no location coordinates leave Home Assistant."""
import asyncio
from datetime import timedelta
import logging

from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import callback
from homeassistant.helpers.event import async_track_time_interval

from .const import DOMAIN
from .monitoring import resolve_monitored_locations
from .official_sources.canada.owner import get_canada_owner

_LOGGER = logging.getLogger(__name__)


class CanadaRuntime:
    """One task across entries; listener lifetime follows enabled entities."""
    def __init__(self, hass, owner):
        self.hass, self.owner = hass, owner
        self._listeners = {}
        self._timer = None
        self._task = None
        self._stopping = False
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, self.async_stop)

    @callback
    def attach(self, entry, listener, *, consumer="diagnostic"):
        self._listeners[(entry.entry_id, consumer)] = (entry, listener)
        if self._timer is None and not self._stopping:
            # Timer checks eligibility only; the owner enforces >=one hour successful requests.
            self._timer = async_track_time_interval(self.hass, self.request_refresh, timedelta(minutes=1))
        self.request_refresh()

    def eligible(self, entry):
        return (any(key[0] == entry.entry_id for key in self._listeners) and not self._stopping
                and any(loc.enabled for loc in resolve_monitored_locations(self.hass, entry)))

    @property
    def enabled(self):
        return any(self.eligible(e) for e, _ in self._listeners.values())

    @callback
    def request_refresh(self, _now=None):
        if self._stopping or not self.enabled:
            if self._task is not None and not self._task.done():
                self._task.cancel()
            self.notify()
            return
        if self._task is None or self._task.done():
            self._task = self.hass.async_create_background_task(self._run(), 'Canada shared refresh')
            self._task.add_done_callback(self._finished)

    def _finished(self, task):
        if not task.cancelled() and task.exception() is not None:
            _LOGGER.error('Canada task failed; source remains paused for review')
        self.notify()

    async def _run(self):
        if not self.enabled:
            return
        try:
            await self.owner.async_refresh(enabled=True, has_enabled_locations=True, allow_uninitialized=True)
        except (OSError, ValueError):
            # Owner diagnostics provide fixed codes; never publish raw source/disk data.
            pass

    @callback
    def notify(self):
        for entry, listener in tuple(self._listeners.values()):
            listener()

    async def _cancel_refresh(self):
        if self._task is not None and not self._task.done():
            self._task.cancel()
            # Do not cancel a durable disk write to make unload look immediate.
            done, _ = await asyncio.wait({self._task}, timeout=5)
            if not done:
                _LOGGER.warning('Canada storage task remains owned during shutdown; source is paused')

    async def detach(self, entry, *, consumer="diagnostic"):
        self._listeners.pop((entry.entry_id, consumer), None)
        if not self._listeners:
            if self._timer is not None:
                self._timer()
                self._timer = None
            await self._cancel_refresh()
        elif not self.enabled:
            await self._cancel_refresh()

    async def async_stop(self, _event=None):
        self._stopping = True
        if self._timer is not None:
            self._timer()
            self._timer = None
        await self._cancel_refresh()


def get_canada_runtime(hass):
    data = hass.data.setdefault(DOMAIN, {})
    if 'canada_runtime' not in data:
        data['canada_runtime'] = CanadaRuntime(hass, get_canada_owner(hass))
    return data['canada_runtime']
