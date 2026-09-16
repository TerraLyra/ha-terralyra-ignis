"""Passive NIFC diagnostics; reading this entity never requests source data."""
import math
import time

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN


class NifcDiagnosticSensor(SensorEntity):
    """Expose shared in-memory state, independently of satellite polling."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False
    _attr_translation_key = 'nifc_source_status'
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ['not_requested', 'available', 'waiting', 'retained_response', 'review_required']
    _attr_icon = 'mdi:information-outline'

    def __init__(self, entry, owner):
        self._owner = owner
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
        return {**self._owner.diagnostics(), 'retrieval_enabled': False,
                'activation_status': 'runtime_activation_pending',
                'national_completeness': 'not_established'}

    async def async_update(self):
        """HA polling only rereads memory; no initialization, I/O or refresh."""
