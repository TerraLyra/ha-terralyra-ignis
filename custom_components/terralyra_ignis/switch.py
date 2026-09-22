"""Explicit opt-in control for NIFC official report map markers."""
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN
from .nifc_map import get_nifc_map
from .canada_map import get_canada_map


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([NifcMapSwitch(hass, entry), CanadaMapSwitch(hass, entry)])


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
                'source_freshness': 'not_established'}


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
                'source_freshness': 'not_established'}
