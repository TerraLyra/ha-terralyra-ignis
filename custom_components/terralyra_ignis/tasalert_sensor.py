"""Disabled-by-default TasALERT diagnostics; enabling is explicit retrieval opt-in."""
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.device_registry import DeviceInfo
from .const import DOMAIN
from .tasalert_runtime import get_tasalert_runtime


class TasAlertDiagnosticSensor(SensorEntity):
    _attr_should_poll=False
    _attr_has_entity_name=True
    _attr_entity_registry_enabled_default=False
    _attr_entity_category=EntityCategory.DIAGNOSTIC
    _attr_translation_key='tasalert_source_status'
    _attr_icon='mdi:information-outline'

    def __init__(self,entry,runtime):
        self.entry,self.runtime=entry,runtime
        self._attached=False
        self._attr_unique_id=f'{entry.entry_id}_tasalert_source_status'
        self._attr_device_info=DeviceInfo(identifiers={(DOMAIN,entry.entry_id)})

    @property
    def native_value(self):
        owner=self.runtime.owner
        if owner.blocked:return 'review_required'
        if owner.initialization_required:return 'initialization_required'
        return owner.state.response.status if owner.state else 'not_requested'

    @property
    def extra_state_attributes(self):
        state=self.runtime.owner.state
        return {'retrieval_enabled':self._attached and self.runtime.enabled,
                'next_attempt':state.response.next_attempt.isoformat() if state and state.response.next_attempt else None,
                'retained_record_count':len(state.ledger) if state else None,
                'review_record_count':len(state.review) if state else None,
                'source_freshness':'not_established','attribution':'TasALERT',
                'license_url':'https://creativecommons.org/licenses/by/4.0/'}

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self._attached=True
        self.runtime.attach(self.entry,self.async_write_ha_state)

    async def async_will_remove_from_hass(self):
        self._attached=False
        await self.runtime.detach(self.entry)
        await super().async_will_remove_from_hass()

    async def async_update(self):
        if self._attached:self.runtime.request_refresh()
