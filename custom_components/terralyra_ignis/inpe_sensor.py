"""Opt-in INPE returned-event count; not an active-fire or confirmation counter."""
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_send
from .const import DOMAIN
from .derived_sources.inpe.coordinator import Coordinator
from .derived_sources.inpe.settings import settings


def get_inpe_owner(hass, entry):
    enabled, states = settings(entry.options)
    if not enabled:
        return None
    owners = hass.data.setdefault(DOMAIN, {}).setdefault('inpe_owners', {})
    # Reuse the owner during config-entry reloads, preserving its cooldown.
    key = (entry.entry_id, states)
    owner = owners.get(key)
    if owner is None:
        # Bound owners retained across repeated state reconfiguration.
        if len(owners) >= 27:
            return None
        owner = owners[key] = Coordinator(async_get_clientsession(hass), states)
    return owner


def create_inpe_sensor(hass, entry):
    owner = get_inpe_owner(hass, entry)
    return InpeInventorySensor(entry, owner) if owner is not None else None


class InpeInventorySensor(SensorEntity):
    _attr_has_entity_name = True
    _attr_translation_key = 'inpe_returned_events'
    _attr_icon = 'mdi:map-marker-radius'
    _attr_should_poll = True
    _attr_force_update = False

    def __init__(self, entry, owner):
        self.owner = owner
        self.entry_id = entry.entry_id
        self._attr_unique_id = f'{entry.entry_id}_inpe_returned_events'
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry.entry_id)})

    @property
    def available(self):
        return self.owner.state.response_status == 'success'

    @property
    def native_value(self):
        return len(self.owner.state.records) if self.available else None

    @property
    def extra_state_attributes(self):
        state = self.owner.state
        return {
            'response_status': state.response_status,
            'last_success_at': state.last_success.isoformat() if state.last_success else None,
            'requested_states': list(self.owner.states),
            'coverage_complete': False,
            'provisional': True,
            'source_freshness': 'not_established',
            'geometry_update_basis': 'previous_day',
            'error_code': state.error,
            'attribution': 'INPE / Programa Queimadas',
            'license_url': 'https://creativecommons.org/licenses/by-sa/4.0/',
            'source_url': 'https://data.inpe.br/queimadas/portal/evento-fogo/',
            'modifications': 'State filtering, field selection and cross-state deduplication.',
        }

    async def async_update(self):
        await self.owner.async_refresh()
        if self.hass is not None:
            async_dispatcher_send(self.hass, f"{DOMAIN}_inpe_{self.entry_id}")
