"""Opt-in shared Canada retrieval diagnostics, never an active-fire count."""

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN
from .canada_runtime import get_canada_runtime


class CanadaDiagnosticSensor(SensorEntity):
    """Expose shared in-memory state, independently of satellite polling."""

    _attr_should_poll = False
    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False
    _attr_translation_key = 'canada_source_status'
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ['not_requested', 'available', 'waiting', 'retained_response', 'review_required']
    _attr_icon = 'mdi:information-outline'

    def __init__(self, entry, owner):
        self._owner = owner
        self._entry = entry
        self._runtime = None
        self._attr_unique_id = f'{entry.entry_id}_canada_source_status'
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry.entry_id)})

    @property
    def native_value(self):
        state = self._owner.state
        if self._owner.store.blocked or (state and state.review_required):
            return 'review_required'
        if state is None:
            return 'not_requested'
        if state.last_success is not None:
            return 'available' if state.status == 'available' else 'retained_response'
        return 'waiting'

    @property
    def extra_state_attributes(self):
        state = self._owner.state
        enabled = self._runtime is not None and self._runtime.eligible(self._entry)
        return {**self._owner.diagnostics(), 'retrieval_enabled': enabled,
                'activation_status': ('initialization_required' if enabled and
                    self._owner.initialization_status == 'required' else
                    'enabled' if enabled else 'disabled_or_no_locations'),
                'last_success_at': state.last_success_at.isoformat() if state and state.last_success_at else None,
                'next_attempt': state.next_attempt.isoformat() if state and state.next_attempt else None,
                'source_record_count': len(state.last_success[0]['features']) if state and state.last_success else None,
                'source_freshness': 'not_established',
                'national_completeness': 'not_established',
                'attribution': 'Canadian Forest Service / CWFIS / Natural Resources Canada',
                'license_url': 'https://open.canada.ca/en/open-government-licence-canada'}

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self._runtime = get_canada_runtime(self.hass)
        self._runtime.attach(self._entry, self.async_write_ha_state)

    async def async_will_remove_from_hass(self):
        if self._runtime is not None:
            await self._runtime.detach(self._entry)
            self._runtime = None
        await super().async_will_remove_from_hass()

    async def async_update(self):
        """Manual refresh joins the shared schedule and cannot bypass cooldown."""
        if self._runtime is not None:
            self._runtime.request_refresh()
