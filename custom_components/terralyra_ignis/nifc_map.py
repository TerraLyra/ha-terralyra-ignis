"""Opt-in official report markers, separate from satellite incident entities."""
import asyncio

from homeassistant.components.geo_location import GeolocationEvent
from homeassistant.const import UnitOfLength
from homeassistant.core import callback

from .const import DOMAIN
from .monitoring import resolve_monitored_locations
from .nifc_presentation import project_nifc, record_attributes, record_title
from .nifc_runtime import get_nifc_runtime

NIFC_MAP_SOURCE = f'{DOMAIN}_nifc_reports'
MAX_MAP_MARKERS = 500


class NifcMapManager:
    def __init__(self, hass, entry):
        self.hass, self.entry = hass, entry
        self.runtime = get_nifc_runtime(hass)
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
        self.schedule()

    async def set_enabled(self, enabled):
        self.enabled = enabled
        if enabled:
            self.runtime.attach(self.entry, self.schedule, consumer='map')
        else:
            await self.runtime.detach(self.entry, consumer='map')
        self.schedule()
        if self._task is not None:
            await self._task

    @callback
    def schedule(self):
        self._dirty = True
        if self._task is None or self._task.done():
            self._task = self.hass.async_create_task(self._sync(), 'NIFC map display')

    async def _sync(self):
        while self._dirty:
            self._dirty = False
            state = self.runtime.owner.state
            result = state.last_success if state is not None else None
            rows = ()
            if self.enabled and self._add_entities is not None:
                rows = project_nifc(result, resolve_monitored_locations(self.hass, self.entry))
                self.status = ('not_requested' if result is None else
                               'available' if state.status == 'retrieved' else 'retained_response')
            else:
                self.status = 'disabled'
            self.relevant_count = len(rows)
            if len(rows) > MAX_MAP_MARKERS:
                self.status = 'display_limit_exceeded'
                rows = ()  # Never silently select a misleading subset.
            desired = {item.record.irwin_id: item for item in rows}
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
                    entity = NifcMapRecord(self, item)
                    self.entities[identity] = entity
                    additions.append(entity)
            if additions and self._add_entities is not None:
                self._add_entities(additions)
            if self._control_listener is not None:
                self._control_listener()

    async def close(self):
        await self.set_enabled(False)
        self._add_entities = None


class NifcMapRecord(GeolocationEvent):
    _attr_should_poll = False
    _attr_source = NIFC_MAP_SOURCE
    _attr_unit_of_measurement = UnitOfLength.KILOMETERS

    def __init__(self, manager, item):
        self.manager, self.item = manager, item
        self.added = False
        self.retired = False
        # Dynamic display only: no entity-registry removal or incident history writes.
        identity = item.record.irwin_id.replace('-', '')
        self.entity_id = f'geo_location.ignis_nifc_{manager.entry.entry_id}_{identity}'.lower()

    @property
    def name(self):
        return record_title(self.item, self.manager.hass.config.language)

    @property
    def icon(self):
        return {'wildfire':'mdi:map-marker-alert', 'prescribed_fire':'mdi:fire-circle',
                'incident_complex':'mdi:map-marker-multiple'}[self.item.record.category]

    @property
    def distance(self):
        return self.item.matches[0].distance_km

    @property
    def latitude(self):
        return self.item.record.latitude

    @property
    def longitude(self):
        return self.item.record.longitude

    @property
    def extra_state_attributes(self):
        state = self.manager.runtime.owner.state
        return {**record_attributes(self.item),
                'response_status': state.status if state is not None else 'not_requested',
                'last_success_at': state.received_at.isoformat() if state is not None and state.received_at is not None else None,
                'retention': 'current_source_response_only'}

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self.added = True
        if (self.retired or not self.manager.enabled or self.manager._add_entities is None
                or self.manager.entities.get(self.item.record.irwin_id) is not self):
            # An add queued just before disable must not leave a late marker behind.
            self.hass.async_create_task(self._remove_after_add(), 'Remove disabled NIFC marker')

    async def _remove_after_add(self):
        # Let EntityPlatform finish its initial state write before removing it.
        await asyncio.sleep(0)
        await self.async_remove()

    async def async_will_remove_from_hass(self):
        self.added = False
        if self.manager.entities.get(self.item.record.irwin_id) is self:
            self.manager.entities.pop(self.item.record.irwin_id)
        if self.manager.enabled:
            # Reuse the stable entity ID only after HA finishes the old removal.
            asyncio.get_running_loop().call_soon(self.manager.schedule)
        await super().async_will_remove_from_hass()


def get_nifc_map(hass, entry):
    managers = hass.data.setdefault(DOMAIN, {}).setdefault('nifc_maps', {})
    if entry.entry_id not in managers:
        managers[entry.entry_id] = NifcMapManager(hass, entry)
    else:
        managers[entry.entry_id].entry = entry
    return managers[entry.entry_id]
