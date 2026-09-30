"""Bounded lifecycle owner for explicitly opted-in location forecasts."""
from __future__ import annotations

import asyncio
import hashlib
from collections.abc import Callable
from datetime import datetime
from functools import partial

from aiohttp import ClientSession
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_call_later

from .core.locations import MonitoredLocation
from .fire_risk_planning import LocationForecastSettings, plan_location_forecasts
from .fire_risk_request_state import PersistentForecastRequestGate
from .location_fire_risk_coordinator import LocationFireRiskCoordinator


class LocationForecastRuntime:
    """Own delayed startup, periodic listeners and shutdown for one entry.

    Integration setup supplies the installation-wide shared provider gate. Reconfiguration closes this owner
    before constructing a replacement; no history or storage is removed.
    """

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, session: ClientSession,
                 locations: tuple[MonitoredLocation, ...],
                 settings: tuple[LocationForecastSettings, ...],
                 gate: PersistentForecastRequestGate) -> None:
        plans = plan_location_forecasts(locations, settings)
        self._hass, self._entry = hass, entry
        self.coordinators = {
            context.location_id: LocationFireRiskCoordinator(hass, entry, session, context, gate)
            for plan in plans for context in plan.contexts
        }
        self._unsub: list[Callable[[], None]] = []
        self._tasks: set[asyncio.Task] = set()
        self._started = False
        self._closed = False

    @callback
    def start(self) -> None:
        """Schedule once, not one burst at integration setup/restart."""
        if self._started or self._closed:
            return
        self._started = True
        # Respect HA's integration polling preference even for the initial fetch.
        if self._entry.pref_disable_polling:
            return
        for index, (location_id, coordinator) in enumerate(sorted(self.coordinators.items())):
            self._unsub.append(coordinator.async_add_listener(lambda: None))
            digest = hashlib.sha256(f"{self._entry.entry_id}:{location_id}".encode()).digest()
            delay = 30 + index * 30 + int.from_bytes(digest[:2]) % 15
            self._unsub.append(async_call_later(
                self._hass, delay, partial(self._start_refresh, coordinator)))

    @callback
    def _start_refresh(self, coordinator: LocationFireRiskCoordinator, _now: datetime) -> None:
        if self._closed:
            return
        task = self._entry.async_create_background_task(
            self._hass, coordinator.async_refresh(),
            f"IGNIS location forecast {coordinator.context.location_id}")
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def close(self) -> None:
        """Cancel pending startup, polling and in-flight operations; keep stores."""
        self._closed = True
        for unsubscribe in self._unsub:
            unsubscribe()
        self._unsub.clear()
        tasks = tuple(self._tasks)
        for task in tasks:
            task.cancel()
        await asyncio.gather(
            *(coordinator.async_shutdown() for coordinator in self.coordinators.values()),
            *tasks, return_exceptions=True)
        self._tasks.clear()
