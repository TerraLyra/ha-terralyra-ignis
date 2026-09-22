"""Canada official displays preserve location and timestamp semantics."""
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from custom_components.terralyra_ignis.canada_calendar import CanadaCalendar, render_canada_events
from custom_components.terralyra_ignis.canada_map import CanadaMapRecord, get_canada_map
from custom_components.terralyra_ignis.canada_presentation import project_canada, record_key
from custom_components.terralyra_ignis.core.locations import MonitoredLocation
from custom_components.terralyra_ignis.official_sources.canada.retry import RefreshState
from pytest_homeassistant_custom_component.common import MockConfigEntry
from custom_components.terralyra_ignis.const import DOMAIN


def sample():
    return ({'features': [{'properties': {
        'national_fire_id': '2026_BC_123', 'agency_code': 'BC',
        'status_date': '2026-09-21T12:00:00Z', 'situation_report_date': '2020-01-01T00:00:00Z',
        'record_start': '2026-09-21T13:00:00Z', 'record_end': '9999-12-31T00:00:00Z',
        'percent_contained': -1, 'stage_of_control_status': 'NEW', 'fire_was_prescribed': -1},
        'geometry': {'type': 'Point', 'coordinates': [-120, 50]}}]}, {})


def places():
    return (MonitoredLocation('home', 'Home', 47, 19, 50, True, 'manual'),
            MonitoredLocation('canada', 'Canada', 50, -120, 50, True, 'manual'))


def test_calendar_uses_status_timestamp_and_half_open_range():
    start = datetime(2026, 9, 21, 12, tzinfo=UTC)
    end = datetime(2026, 9, 22, tzinfo=UTC)
    events = render_canada_events(sample(), places(), start, end, language='hu')
    assert len(events) == 1
    assert events[0].start == start
    assert (events[0].end - events[0].start).total_seconds() == 1
    assert 'nem gyulladási idő' in events[0].description
    assert 'open-government-licence' in events[0].description
    assert render_canada_events(sample(), places(), datetime(2026, 9, 20, tzinfo=UTC), start) == []


def test_marker_distance_identity_and_unknown_status(hass):
    item, = project_canada(sample(), places())
    manager = SimpleNamespace(entry=SimpleNamespace(entry_id='entry'), hass=hass,
                              runtime=SimpleNamespace(owner=SimpleNamespace(state=None)))
    marker = CanadaMapRecord(manager, item)
    assert marker.distance == 0
    assert marker.latitude == 50
    assert marker.longitude == -120
    assert marker.extra_state_attributes['distance_reference_id'] == 'canada'
    assert marker.extra_state_attributes['stage_of_control'] == 'unknown'
    changed = sample()
    changed[0]['features'][0]['id'] = 'unstable_transport_id'
    assert record_key(project_canada(changed, places())[0]) == record_key(item)
    assert not project_canada(sample(), places()[:1])


async def test_calendar_default_and_map_disable_preserve_source(hass):
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)
    calendar = CanadaCalendar(hass, entry)
    assert calendar.entity_registry_enabled_default is False
    assert calendar.event is None
    manager = get_canada_map(hass, entry)
    source = sample()
    manager.runtime.owner.state = RefreshState(last_success=source, status='available')
    added = []
    with patch('custom_components.terralyra_ignis.canada_map.resolve_monitored_locations', return_value=places()), patch.object(manager.runtime, 'attach'), patch.object(manager.runtime, 'detach', new_callable=AsyncMock):
        manager.bind(added.extend)
        await manager.set_enabled(True)
        assert len(added) == 1
        marker = added[0]
        marker.added = True
        marker.async_remove = AsyncMock()
        await manager.set_enabled(False)
        marker.async_remove.assert_awaited_once()
        assert manager.runtime.owner.state.last_success is source
        assert manager.status == 'disabled'
    await manager.runtime.async_stop()
