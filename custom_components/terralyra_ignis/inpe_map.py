"""Opt-in derived-event markers, separate from satellite incident entities."""
import asyncio

from homeassistant.components.geo_location import GeolocationEvent
from homeassistant.const import UnitOfLength
from homeassistant.core import callback

from .const import DOMAIN
from .monitoring import resolve_monitored_locations
from .inpe_presentation import project_inpe, record_attributes, record_title, record_key
from .inpe_sensor import get_inpe_owner
from homeassistant.helpers.dispatcher import async_dispatcher_connect

INPE_MAP_SOURCE = f'{DOMAIN}_inpe_reports'
MAX_MAP_MARKERS = 500


class InpeMapManager:
    def __init__(self, hass, entry):
        self.hass, self.entry = hass, entry
        self.owner = get_inpe_owner(hass, entry)
        self._unsubscribe = None
        self.enabled = False
        self.status = 'disabled'
        self.relevant_count = 0
        self.entities = {}
        self._add_entities = None
        self._task = None
        self._dirty = False
        self._control_listener = None

    @callback
    def bind(self, add_entities):
        self._add_entities = add_entities
        if self._unsubscribe is None:
            self._unsubscribe = async_dispatcher_connect(self.hass, f"{DOMAIN}_inpe_{self.entry.entry_id}", self.schedule)
        self.schedule()

    async def set_enabled(self, enabled):
        self.enabled = bool(enabled and self.owner is not None)
        self.schedule()
        if self._task is not None:
            await self._task

    @callback
    def schedule(self):
        self._dirty = True
        if self._task is None or self._task.done():
            self._task = self.hass.async_create_task(self._sync(), 'INPE map display')

    async def _sync(self):
        while self._dirty:
            self._dirty = False
            state = self.owner.state if self.owner else None
            result = state
            rows = ()
            if self.enabled and self._add_entities is not None:
                rows = project_inpe(result, resolve_monitored_locations(self.hass, self.entry))
                self.status = ('not_requested' if result is None else
                               'available' if state.response_status == 'success' else 'unavailable')
            else:
                self.status = 'disabled'
            self.relevant_count = len(rows)
            if len(rows) > MAX_MAP_MARKERS:
                self.status = 'display_limit_exceeded'
                rows = ()  # Never silently select a misleading subset.
            desired = {record_key(item): item for item in rows}
            for identity in tuple(self.entities):
                if identity not in desired:
                    entity = self.entities[identity]
                    entity.retired = True
                    if entity.added:
                        await entity.async_remove()
            additions = []
            for identity, item in desired.items():
                if identity in self.entities:
                    entity = self.entities[identity]
                    if entity.retired:
                        continue  # Late queued add must finish removal before reuse.
                    entity.item = item
                    if entity.added:
                        entity.async_write_ha_state()
                else:
                    entity = InpeMapRecord(self, item)
                    self.entities[identity] = entity
                    additions.append(entity)
            if additions and self._add_entities is not None:
                self._add_entities(additions)
            if self._control_listener is not None:
                self._control_listener()

    async def close(self):
        await self.set_enabled(False)
        self._add_entities = None
        if self._unsubscribe is not None:
            self._unsubscribe()
            self._unsubscribe = None


class InpeMapRecord(GeolocationEvent):
    _attr_should_poll = False
    _attr_source = INPE_MAP_SOURCE
    _attr_unit_of_measurement = UnitOfLength.KILOMETERS

    def __init__(self, manager, item):
        self.manager, self.item = manager, item
        self.added = False
        self.retired = False
        # Dynamic display only: no entity-registry removal or incident history writes.
        identity = record_key(item)
        self.entity_id = f'geo_location.ignis_inpe_{manager.entry.entry_id}_{identity}'.lower()

    @property
    def name(self):
        return record_title(self.item, self.manager.hass.config.language)

    @property
    def icon(self):
        return {'bushfire':'mdi:forest', 'planned_burn':'mdi:fire-circle',
                'structure_fire':'mdi:home-alert'}.get(self.item['category'],'mdi:map-marker-alert')

    @property
    def distance(self):
        return self.item['distance_km']

    @property
    def latitude(self):
        return self.item['latitude']

    @property
    def longitude(self):
        return self.item['longitude']

    @property
    def extra_state_attributes(self):
        state = self.manager.owner.state
        return {**record_attributes(self.item),
                'response_status': state.response_status,
                'last_success_at': state.last_success.isoformat() if state.last_success else None,
                'source_freshness': 'not_established'}

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self.added = True
        if (self.retired or not self.manager.enabled or self.manager._add_entities is None
                or self.manager.entities.get(record_key(self.item)) is not self):
            # An add queued just before disable must not leave a late marker behind.
            self.hass.async_create_task(self._remove_after_add(), 'Remove disabled INPE marker')

    async def _remove_after_add(self):
        # Let EntityPlatform finish its initial state write before removing it.
        await asyncio.sleep(0)
        await self.async_remove()

    async def async_will_remove_from_hass(self):
        self.added = False
        if self.manager.entities.get(record_key(self.item)) is self:
            self.manager.entities.pop(record_key(self.item))
        if self.manager.enabled:
            # Reuse the stable entity ID only after HA finishes the old removal.
            asyncio.get_running_loop().call_soon(self.manager.schedule)
        await super().async_will_remove_from_hass()


def get_inpe_map(hass, entry):
    managers = hass.data.setdefault(DOMAIN, {}).setdefault('inpe_maps', {})
    if entry.entry_id not in managers:
        managers[entry.entry_id] = InpeMapManager(hass, entry)
    else:
        managers[entry.entry_id].entry = entry
        managers[entry.entry_id].owner = get_inpe_owner(hass, entry)
    return managers[entry.entry_id]
