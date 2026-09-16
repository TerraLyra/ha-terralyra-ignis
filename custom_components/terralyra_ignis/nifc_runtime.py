"""Shared opt-in scheduler; no location coordinates leave Home Assistant."""
import asyncio
from datetime import timedelta
import logging

from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import callback
from homeassistant.helpers.event import async_track_time_interval

from .const import DOMAIN
from .monitoring import resolve_monitored_locations
from .official_sources.nifc.owner import get_nifc_owner
from .repairs import async_sync_nifc_research_issue

_LOGGER = logging.getLogger(__name__)


class NifcRuntime:
    """One task across entries; listener lifetime follows enabled entities."""
    def __init__(self, hass, owner):
        self.hass, self.owner = hass, owner
        self._listeners = {}
        self._timer = None
        self._task = None
        self._stopping = False
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, self.async_stop)

    @callback
    def attach(self, entry, listener):
        self._listeners[entry.entry_id] = (entry, listener)
        if self._timer is None and not self._stopping:
            # Timer checks eligibility only; the owner enforces >=15 minute requests.
            self._timer = async_track_time_interval(self.hass, self.request_refresh, timedelta(minutes=1))
        self.request_refresh()

    def eligible(self, entry):
        return (entry.entry_id in self._listeners and not self._stopping
                and any(loc.enabled for loc in resolve_monitored_locations(self.hass, entry)))

    @callback
    def request_refresh(self, _now=None):
        if self._stopping or not any(self.eligible(e) for e, _ in self._listeners.values()):
            if self._task is not None and not self._task.done():
                self._task.cancel()
            self.notify()
            return
        if self._task is None or self._task.done():
            self._task = self.hass.async_create_background_task(self._run(), 'NIFC shared refresh')
            self._task.add_done_callback(self._finished)

    def _finished(self, task):
        if not task.cancelled() and task.exception() is not None:
            _LOGGER.error('NIFC task failed; source remains paused for review')
        self.notify()

    async def _run(self):
        if not any(self.eligible(e) for e, _ in self._listeners.values()):
            return
        try:
            await self.owner.async_refresh(enabled=True, has_enabled_locations=True, allow_uninitialized=True)
        except (OSError, ValueError):
            # Owner diagnostics provide fixed codes; never publish raw source/disk data.
            pass

    @callback
    def notify(self):
        for entry, listener in tuple(self._listeners.values()):
            async_sync_nifc_research_issue(self.hass, entry, enabled=True,
                                          problem=self.owner.diagnostics()['problem'])
            listener()

    async def _cancel_refresh(self):
        if self._task is not None and not self._task.done():
            self._task.cancel()
            # Do not cancel a durable disk write to make unload look immediate.
            done, _ = await asyncio.wait({self._task}, timeout=5)
            if not done:
                _LOGGER.warning('NIFC storage task remains owned during shutdown; source is paused')

    async def detach(self, entry):
        self._listeners.pop(entry.entry_id, None)
        async_sync_nifc_research_issue(self.hass, entry, enabled=False)
        if not self._listeners:
            if self._timer is not None:
                self._timer()
                self._timer = None
            await self._cancel_refresh()
        elif not any(self.eligible(e) for e, _ in self._listeners.values()):
            await self._cancel_refresh()

    async def async_stop(self, _event=None):
        self._stopping = True
        if self._timer is not None:
            self._timer()
            self._timer = None
        await self._cancel_refresh()


def get_nifc_runtime(hass):
    data = hass.data.setdefault(DOMAIN, {})
    if 'nifc_runtime' not in data:
        data['nifc_runtime'] = NifcRuntime(hass, get_nifc_owner(hass))
    return data['nifc_runtime']
