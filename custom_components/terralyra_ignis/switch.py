"""Explicit opt-in control for NIFC official report map markers."""
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN
from .nifc_map import get_nifc_map
from .canada_map import get_canada_map
from .tasalert_map import get_tasalert_map
from .inpe_map import get_inpe_map
from .derived_sources.inpe.settings import settings as inpe_settings


async def async_setup_entry(hass, entry, async_add_entities):
    entities = [NifcMapSwitch(hass, entry), CanadaMapSwitch(hass, entry), TasAlertMapSwitch(hass, entry)]
    if inpe_settings(entry.options)[0]:
        entities.append(InpeMapSwitch(hass, entry))
    async_add_entities(entities)


class NifcMapSwitch(SwitchEntity, RestoreEntity):
    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_translation_key = 'nifc_map'
    _attr_icon = 'mdi:map-marker-outline'
    _attr_is_on = False

    def __init__(self, hass, entry):
        self._manager = get_nifc_map(hass, entry)
        self._attr_unique_id = f'{entry.entry_id}_nifc_map'
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry.entry_id)})

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self._manager._control_listener = self.async_write_ha_state
        previous = await self.async_get_last_state()
        if previous is not None and previous.state == 'on':
            self._attr_is_on = True
            await self._manager.set_enabled(True)

    async def async_will_remove_from_hass(self):
        self._manager._control_listener = None
        await self._manager.set_enabled(False)
        await super().async_will_remove_from_hass()

    async def async_turn_on(self, **kwargs):
        self._attr_is_on = True
        await self._manager.set_enabled(True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        self._attr_is_on = False
        await self._manager.set_enabled(False)
        self.async_write_ha_state()

    @property
    def extra_state_attributes(self):
        return {**self._manager.runtime.owner.diagnostics(), 'map_status': self._manager.status,
                'matched_source_records': self._manager.relevant_count,
                'visible_markers': sum(not entity.retired for entity in self._manager.entities.values()),
                'source_freshness': 'not_established',
                'ignis_map_source': 'terralyra_ignis_nifc_reports'}


class CanadaMapSwitch(SwitchEntity, RestoreEntity):
    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_translation_key = 'canada_map'
    _attr_icon = 'mdi:map-marker-outline'
    _attr_is_on = False

    def __init__(self, hass, entry):
        self._manager = get_canada_map(hass, entry)
        self._attr_unique_id = f'{entry.entry_id}_canada_map'
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry.entry_id)})

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self._manager._control_listener = self.async_write_ha_state
        previous = await self.async_get_last_state()
        if previous is not None and previous.state == 'on':
            self._attr_is_on = True
            await self._manager.set_enabled(True)

    async def async_will_remove_from_hass(self):
        self._manager._control_listener = None
        await self._manager.set_enabled(False)
        await super().async_will_remove_from_hass()

    async def async_turn_on(self, **kwargs):
        self._attr_is_on = True
        await self._manager.set_enabled(True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        self._attr_is_on = False
        await self._manager.set_enabled(False)
        self.async_write_ha_state()

    @property
    def extra_state_attributes(self):
        return {**self._manager.runtime.owner.diagnostics(), 'map_status': self._manager.status,
                'matched_source_records': self._manager.relevant_count,
                'visible_markers': sum(not entity.retired for entity in self._manager.entities.values()),
                'source_freshness': 'not_established',
                'ignis_map_source': 'terralyra_ignis_canada_reports'}


class TasAlertMapSwitch(SwitchEntity, RestoreEntity):
    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_translation_key = 'tasalert_map'
    _attr_icon = 'mdi:map-marker-outline'
    _attr_is_on = False

    def __init__(self, hass, entry):
        self._manager = get_tasalert_map(hass, entry)
        self._attr_unique_id = f'{entry.entry_id}_tasalert_map'
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry.entry_id)})

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self._manager._control_listener = self.async_write_ha_state
        previous = await self.async_get_last_state()
        if previous is not None and previous.state == 'on':
            self._attr_is_on = True
            await self._manager.set_enabled(True)

    async def async_will_remove_from_hass(self):
        self._manager._control_listener = None
        await self._manager.set_enabled(False)
        await super().async_will_remove_from_hass()

    async def async_turn_on(self, **kwargs):
        self._attr_is_on = True
        await self._manager.set_enabled(True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        self._attr_is_on = False
        await self._manager.set_enabled(False)
        self.async_write_ha_state()

    @property
    def extra_state_attributes(self):
        return {**self._manager.runtime.owner.diagnostics(), 'map_status': self._manager.status,
                'matched_source_records': self._manager.relevant_count,
                'visible_markers': sum(not entity.retired for entity in self._manager.entities.values()),
                'source_freshness': 'not_established',
                'ignis_map_source': 'terralyra_ignis_tasalert_reports'}


class InpeMapSwitch(NifcMapSwitch):
    """Map-only visibility; source opt-in remains in integration options."""
    _attr_translation_key = 'inpe_map'

    def __init__(self, hass, entry):
        self._manager = get_inpe_map(hass, entry)
        self._attr_unique_id = f'{entry.entry_id}_inpe_map'
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry.entry_id)})

    @property
    def extra_state_attributes(self):
        state = self._manager.owner.state if self._manager.owner else None
        return {'ignis_map_source': 'terralyra_ignis_inpe_reports',
                'response_status': state.response_status if state else 'not_requested',
                'last_success_at': state.last_success.isoformat() if state and state.last_success else None,
                'map_status': self._manager.status,
                'visible_markers': sum(not e.retired for e in self._manager.entities.values()),
                'matched_source_records': self._manager.relevant_count,
                'source_freshness': 'not_established', 'coverage_complete': False}
