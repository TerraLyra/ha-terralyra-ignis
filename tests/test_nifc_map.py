"""Map lifecycle changes HA display state only, never the incident archive."""
import asyncio
import logging
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock, patch

from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers.storage import Store
from homeassistant.config_entries import ConfigEntryState
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.terralyra_ignis.const import DOMAIN
from custom_components.terralyra_ignis.nifc_map import get_nifc_map
from custom_components.terralyra_ignis.official_sources.nifc.refresh import RefreshState
from test_nifc_presentation import LOC, RECORD, result


async def test_map_enable_update_disable_does_not_delete_history(hass,hass_storage):
    entry=MockConfigEntry(domain=DOMAIN);entry.add_to_hass(hass)
    entry.mock_state(hass,ConfigEntryState.LOADED)
    manager=get_nifc_map(hass,entry)
    state=RefreshState(last_success=result(RECORD),status='retrieved',received_at=datetime(2026,9,24,9,tzinfo=timezone.utc))
    manager.runtime.owner.coordinator._inner=SimpleNamespace(state=state)
    history=Store(hass,1,'synthetic_map_history');await history.async_save({'keep':['incident']})
    component=EntityComponent(logging.getLogger(__name__),'geo_location',hass)
    with patch.object(manager.runtime,'request_refresh'), patch('custom_components.terralyra_ignis.nifc_map.resolve_monitored_locations',return_value=(LOC,)):
        manager.bind(lambda entities: hass.async_create_task(component.async_add_entities(entities)))
        await manager._task
        assert not manager.entities
        await manager.set_enabled(True)
        await hass.async_block_till_done()
        assert len(manager.entities)==1
        entity=next(iter(manager.entities.values()))
        assert hass.states.get(entity.entity_id).attributes['distance_reference_id']=='california'
        assert float(hass.states.get(entity.entity_id).state)==0
        assert hass.states.get(entity.entity_id).attributes['last_success_at']=='2026-09-24T09:00:00+00:00'
        await manager.set_enabled(False)
        await hass.async_block_till_done()
        assert hass.states.get(entity.entity_id) is None
        assert not manager.entities
        assert await history.async_load()=={'keep':['incident']}
        await manager.close()


async def test_late_queued_add_after_disable_is_removed(hass,hass_storage):
    entry=MockConfigEntry(domain=DOMAIN);entry.add_to_hass(hass)
    manager=get_nifc_map(hass,entry)
    manager.runtime.owner.coordinator._inner=SimpleNamespace(state=RefreshState(last_success=result(RECORD),status='retrieved'))
    queued=[]
    component=EntityComponent(logging.getLogger(__name__),'geo_location',hass)
    with patch.object(manager.runtime,'request_refresh'), patch('custom_components.terralyra_ignis.nifc_map.resolve_monitored_locations',return_value=(LOC,)):
        manager.bind(queued.extend)
        await manager.set_enabled(True)
        assert len(queued)==1
        await manager.set_enabled(False)
        await component.async_add_entities(queued)
        await hass.async_block_till_done()
        assert not manager.entities
        assert hass.states.get(queued[0].entity_id) is None
        await manager.close()


async def test_excess_markers_are_reported_not_silently_truncated(hass):
    from dataclasses import replace
    entry=MockConfigEntry(domain=DOMAIN);entry.add_to_hass(hass)
    manager=get_nifc_map(hass,entry)
    records=[replace(RECORD,irwin_id=f'12345678-1234-1234-1234-{n:012d}') for n in range(501)]
    manager.runtime.owner.coordinator._inner=SimpleNamespace(state=RefreshState(last_success=result(*records),status='retrieved'))
    queued=[]
    with patch.object(manager.runtime,'request_refresh'), patch('custom_components.terralyra_ignis.nifc_map.resolve_monitored_locations',return_value=(LOC,)):
        manager.bind(queued.extend)
        await manager.set_enabled(True)
        assert manager.status=='display_limit_exceeded'
        assert manager.relevant_count==501
        assert not queued and not manager.entities
        await manager.close()


async def test_rapid_reenable_keeps_one_stable_marker(hass):
    entry=MockConfigEntry(domain=DOMAIN);entry.add_to_hass(hass)
    manager=get_nifc_map(hass,entry)
    manager.runtime.owner.coordinator._inner=SimpleNamespace(state=RefreshState(last_success=result(RECORD),status='retrieved'))
    queued=[]
    component=EntityComponent(logging.getLogger(__name__),'geo_location',hass)
    with patch.object(manager.runtime,'request_refresh'), patch('custom_components.terralyra_ignis.nifc_map.resolve_monitored_locations',return_value=(LOC,)):
        manager.bind(queued.extend)
        await manager.set_enabled(True)
        first=queued[0]
        await manager.set_enabled(False)
        await manager.set_enabled(True)
        await component.async_add_entities([first])
        await hass.async_block_till_done()
        assert len(queued)==2
        assert hass.states.get(first.entity_id) is None
        await component.async_add_entities([queued[1]])
        await hass.async_block_till_done()
        assert queued[1].entity_id==first.entity_id
        assert len(manager.entities)==1
        assert hass.states.get(first.entity_id) is not None
        await manager.close()
        await hass.async_block_till_done()
        assert hass.states.get(first.entity_id) is None
