"""Opt-in timed source-record calendar, not ignition or fire-duration history."""
from datetime import timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN
from .monitoring import resolve_monitored_locations
from .nifc_presentation import ATTRIBUTION, LABELS, SOURCE_URL, project_nifc, record_title
from .nifc_runtime import get_nifc_runtime


def render_nifc_events(result, locations, start, end, *, language='en', retained=False):
    if any(value.tzinfo is None or value.utcoffset() is None for value in (start, end)) or end <= start:
        raise ValueError('Timezone-aware positive calendar range required')
    labels = LABELS.get(language, LABELS['en'])
    events = []
    for item in project_nifc(result, locations):
        record = item.record
        stamp = record.modified_at or record.discovered_at
        if stamp is None:
            continue
        # A one-second UI marker is explicitly not a duration assertion.
        try:
            marker_end = stamp + timedelta(seconds=1)
        except OverflowError:
            continue
        if stamp >= end or marker_end <= start:
            continue
        basis = 'modified' if record.modified_at else 'discovered'
        note = ("A forrás időbélyege; nem következtetett gyulladási idő. Az egy másodperc "
                "csak megjelenítési jelölő, nem a tűz időtartama. Nem műholdas észlelés."
                if language == 'hu' else
                "Source timestamp, not inferred ignition. One second is a display marker, "
                "not fire duration. This is not a satellite detection.")
        status = ('Megőrzött korábbi válasz' if language == 'hu' else 'Retained earlier response') if retained else (
            'Letöltött forrásjelentés; az aktuális tűzállapot nem igazolt' if language == 'hu' else
            'Downloaded source report; current fire activity is not established')
        lines = [ATTRIBUTION, SOURCE_URL, note, status,
                 f"{labels[basis]}: {stamp.isoformat()}",
                 f"IRWIN: {record.irwin_id}",
                 f"Complex: {item.complex_role}; parent: {record.parent_complex_id or '—'}",
                 'Locations: ' + ', '.join(f'{m.name} ({m.distance_km:.1f} km)' for m in item.matches),
                 f"Discovery: {record.discovered_at.isoformat() if record.discovered_at else '—'}",
                 f"Modified: {record.modified_at.isoformat() if record.modified_at else '—'}"]
        events.append(CalendarEvent(summary=f'{record_title(item, language)} · {labels[basis]}',
            start=stamp, end=marker_end, description='\n'.join(lines),
            uid=f'nifc-{record.irwin_id}'))
    return sorted(events, key=lambda event: (event.start, event.uid))


class NifcCalendar(CalendarEntity):
    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_entity_registry_enabled_default = False
    _attr_translation_key = 'nifc_reports'
    _attr_icon = 'mdi:calendar-text'

    def __init__(self, hass, entry):
        self._entry = entry
        self._runtime = get_nifc_runtime(hass)
        self._attr_unique_id = f'{entry.entry_id}_nifc_reports'
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
        result = state.last_success if state is not None else None
        rows = project_nifc(result, resolve_monitored_locations(self.hass, self._entry)) if self.hass else ()
        return {**self._runtime.owner.diagnostics(), 'attribution': ATTRIBUTION,
                'undated_matched_source_records': sum(item.record.modified_at is None and
                    item.record.discovered_at is None for item in rows),
                'unlocated_source_records': sum(record.latitude is None or record.longitude is None
                    for record in result.records) if result is not None else None,
                'retention': 'current_source_response_only', 'date_basis': 'modified_then_discovery',
                'marker_duration_seconds': 1}

    async def async_get_events(self, hass, start_date, end_date):
        self._runtime.request_refresh()
        locations = resolve_monitored_locations(hass, self._entry)
        if not any(location.enabled for location in locations):
            return []
        state = self._runtime.owner.state
        if state is None or state.last_success is None:
            raise HomeAssistantError('NIFC has no validated response yet; check source diagnostics')
        return render_nifc_events(state.last_success, locations,
            start_date, end_date, language=hass.config.language, retained=state.status != 'retrieved')
