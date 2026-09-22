"""Opt-in timed source-record calendar, not ignition or fire-duration history."""
from datetime import datetime, timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN
from .monitoring import resolve_monitored_locations
from .canada_presentation import ATTRIBUTION, LICENSE_URL, SOURCE_URL, project_canada, record_title, record_key
from .canada_runtime import get_canada_runtime


def render_canada_events(result, locations, start, end, *, language='en', retained=False):
    if any(value.tzinfo is None or value.utcoffset() is None for value in (start, end)) or end <= start:
        raise ValueError('Timezone-aware positive calendar range required')
    events = []
    label = 'Jelentett állapot frissítése' if language == 'hu' else 'Reported status update'
    for item in project_canada(result, locations):
        stamp = datetime.fromisoformat(item['source_times']['status_date'])
        try:
            marker_end = stamp + timedelta(seconds=1)
        except OverflowError:
            continue
        if stamp >= end or marker_end <= start:
            continue
        note = ('A forrás állapotjelentésének időpontja, nem gyulladási idő. '
                'Az egy másodperc megjelenítési jelölő, nem a tűz időtartama.'
                if language == 'hu' else
                'Source status timestamp, not ignition. One second is a display marker, not fire duration.')
        lines = [ATTRIBUTION, SOURCE_URL, LICENSE_URL, note,
                 'Retained earlier response' if retained else 'Downloaded source report',
                 'Current fire activity is not established; not a satellite detection.',
                 'Locations: ' + ', '.join(f"{m['location_name']} ({m['distance_km']:.1f} km)"
                                            for m in item['location_matches']),
                 *[f'{key}: {value}' for key, value in item['source_times'].items()]]
        events.append(CalendarEvent(summary=f'{record_title(item, language)} · {label}',
            start=stamp, end=marker_end, description='\n'.join(lines),
            uid=f'canada-{record_key(item)}'))
    return sorted(events, key=lambda event: (event.start, event.uid))


class CanadaCalendar(CalendarEntity):
    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_entity_registry_enabled_default = False
    _attr_translation_key = 'canada_reports'
    _attr_icon = 'mdi:calendar-text'

    def __init__(self, hass, entry):
        self._entry = entry
        self._runtime = get_canada_runtime(hass)
        self._attr_unique_id = f'{entry.entry_id}_canada_reports'
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry.entry_id)})

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self._runtime.attach(self._entry, self.async_write_ha_state, consumer='calendar')

    async def async_will_remove_from_hass(self):
        await self._runtime.detach(self._entry, consumer='calendar')
        await super().async_will_remove_from_hass()

    @property
    def event(self):
        return None  # A source update is not a current emergency boolean.

    @property
    def extra_state_attributes(self):
        state = self._runtime.owner.state
        return {**self._runtime.owner.diagnostics(), 'attribution': ATTRIBUTION,
                'retention': 'current_source_response_only', 'date_basis': 'status_date',
                'marker_duration_seconds': 1, 'license_url': LICENSE_URL}

    async def async_get_events(self, hass, start_date, end_date):
        self._runtime.request_refresh()
        locations = resolve_monitored_locations(hass, self._entry)
        if not any(location.enabled for location in locations):
            return []
        state = self._runtime.owner.state
        if state is None or state.last_success is None:
            raise HomeAssistantError('Canada has no validated response yet; check source diagnostics')
        return render_canada_events(state.last_success, locations,
            start_date, end_date, language=hass.config.language, retained=state.status != 'available')
