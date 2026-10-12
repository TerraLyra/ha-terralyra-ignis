"""TasALERT projection and isolated HA map lifecycle, with synthetic records."""
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from custom_components.terralyra_ignis.tasalert_map import get_tasalert_map
from custom_components.terralyra_ignis.tasalert_presentation import project_tasalert
from custom_components.terralyra_ignis.core.locations import MonitoredLocation
from custom_components.terralyra_ignis.official_sources.tasalert.engine import Engine, advance
from custom_components.terralyra_ignis.const import DOMAIN
from pytest_homeassistant_custom_component.common import MockConfigEntry


def sample():
    return b'''<kml xmlns="http://www.opengis.net/kml/2.2"><Document><Placemark id="one"><name>Test incident</name><ExtendedData><Data name="feedType"><value>incident</value></Data><Data name="type"><value>Bushfire</value></Data><Data name="status"><value>Going</value></Data><Data name="created"><value>2026-10-12T10:00:00+11:00</value></Data><Data name="changed"><value>2026-10-12T11:00:00+11:00</value></Data></ExtendedData><Point><coordinates>147,-42</coordinates></Point></Placemark></Document></kml>'''


def places():
    return (MonitoredLocation('home','Home',47,19,50,True,'manual'),
            MonitoredLocation('tas','Tasmania',-42,147,50,True,'manual'))


def test_projection_uses_matching_place_and_original_type():
    state=advance(Engine(),datetime(2026,10,12,tzinfo=UTC),200,sample())
    item,=project_tasalert(state,iter(places()))
    assert item['distance_reference_id']=='tas'
    assert item['distance_km']==0
    assert item['category']=='bushfire'
    assert not item['active_fire_verified']
    assert not project_tasalert(state,places()[:1])


async def test_map_disable_removes_markers_not_source(hass):
    entry=MockConfigEntry(domain=DOMAIN);entry.add_to_hass(hass)
    manager=get_tasalert_map(hass,entry)
    state=advance(Engine(),datetime(2026,10,12,tzinfo=UTC),200,sample())
    manager.runtime.owner.state=state
    added=[]
    with patch('custom_components.terralyra_ignis.tasalert_map.resolve_monitored_locations',return_value=places()), patch.object(manager.runtime,'attach'), patch.object(manager.runtime,'detach',new_callable=AsyncMock):
        manager.bind(added.extend)
        await manager.set_enabled(True)
        assert len(added)==1
        marker=added[0]
        assert marker.extra_state_attributes['report_category']=='Bushfire'
        assert marker.extra_state_attributes['license_url'].endswith('/by/4.0/')
        marker.added=True;marker.async_remove=AsyncMock()
        await manager.set_enabled(False)
        marker.async_remove.assert_awaited_once()
        assert manager.runtime.owner.state is state
    await manager.runtime.async_stop()


async def test_real_ha_marker_registration_removal_and_reload(hass,hass_storage):
    import logging
    from homeassistant.helpers.entity_component import EntityComponent
    from homeassistant.helpers.storage import Store
    from custom_components.terralyra_ignis.official_sources.tasalert.owner import TasAlertOwner, STORE_KEY
    entry=MockConfigEntry(domain=DOMAIN);entry.add_to_hass(hass)
    manager=get_tasalert_map(hass,entry)
    owner=manager.runtime.owner
    await owner.async_load(confirmed_new=True)
    state=advance(Engine(),datetime(2026,10,12,tzinfo=UTC),200,sample())
    owner.fetcher=AsyncMock(return_value=state)
    await owner.async_refresh()
    component=EntityComponent(logging.getLogger(__name__),'geo_location',hass)
    def add(entities):
        hass.async_create_task(component.async_add_entities(entities))
    with patch('custom_components.terralyra_ignis.tasalert_map.resolve_monitored_locations',return_value=places()), patch.object(manager.runtime,'attach'), patch.object(manager.runtime,'detach',new_callable=AsyncMock):
        manager.bind(add)
        await manager.set_enabled(True)
        await hass.async_block_till_done()
        marker,=manager.entities.values()
        entity_id=marker.entity_id
        assert hass.states.get(entity_id).attributes['source']=='terralyra_ignis_tasalert_reports'
        assert hass.states.get(entity_id).attributes['distance_reference_id']=='tas'
        await manager.close()
        await hass.async_block_till_done()
        assert hass.states.get(entity_id) is None
        restored=TasAlertOwner(Store(hass,1,STORE_KEY),None)
        await restored.async_load()
        assert restored.state.response.next_attempt==state.response.next_attempt
        manager.runtime.owner=restored
        manager.bind(add)
        await manager.set_enabled(True)
        await hass.async_block_till_done()
        assert hass.states.get(entity_id) is not None
        await manager.close()
        await hass.async_block_till_done()
    await owner.async_close()
    await manager.runtime.async_stop()
