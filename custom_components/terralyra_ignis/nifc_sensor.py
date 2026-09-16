"""Opt-in shared NIFC retrieval diagnostics, never an active-fire count."""
import math
import time

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN
from .nifc_runtime import get_nifc_runtime


class NifcDiagnosticSensor(SensorEntity):
    """Expose shared in-memory state, independently of satellite polling."""

    _attr_should_poll = False
    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False
    _attr_translation_key = 'nifc_source_status'
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ['not_requested', 'available', 'waiting', 'retained_response', 'review_required']
    _attr_icon = 'mdi:information-outline'

    def __init__(self, entry, owner):
        self._owner = owner
        self._entry = entry
        self._runtime = None
        self._attr_unique_id = f'{entry.entry_id}_nifc_source_status'
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry.entry_id)})

    @property
    def native_value(self):
        diagnostics = self._owner.diagnostics()
        state = self._owner.state
        problem = diagnostics['problem']
        if problem not in (None, 'not_loaded', 'refresh_failed_transient', 'refresh_failed_rate_limited'):
            return 'review_required'
        if state is None:
            return 'not_requested'
        if math.isinf(state.next_attempt_at):
            return 'review_required'
        if state.last_success is not None:
            return 'available' if state.status == 'retrieved' else 'retained_response'
        if state.next_attempt_at > time.monotonic():
            return 'waiting'
        return 'not_requested'

    @property
    def extra_state_attributes(self):
        enabled = self._runtime is not None and self._runtime.eligible(self._entry)
        state = self._owner.state
        result = state.last_success if state is not None else None
        categories = {}
        if result is not None:
            for record in result.records:
                categories[record.category] = categories.get(record.category, 0) + 1
        return {**self._owner.diagnostics(), 'retrieval_enabled': enabled,
                'activation_status': ('initialization_required' if enabled and
                    self._owner.initialization_status == 'required' else
                    'enabled' if enabled else 'disabled_or_no_locations'),
                'source_record_count': len(result.records) if result is not None else None,
                'records_by_category': categories,
                'retrieval_method': result.retrieval_method if result else None,
                'receipt_age_seconds': (max(0, round(time.monotonic()-state.last_success_at))
                    if state is not None and state.last_success_at is not None else None),
                'source_freshness': 'not_established',
                'national_completeness': 'not_established',
                'attribution': 'NIFC / WFIGS / IRWIN'}

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self._runtime = get_nifc_runtime(self.hass)
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
