"""INPE map projection and lifecycle use no live provider or incident archive."""
from dataclasses import replace
from datetime import datetime, UTC
import logging
from types import SimpleNamespace
from unittest.mock import patch

from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers.dispatcher import async_dispatcher_send
from pytest_homeassistant_custom_component.common import MockConfigEntry
from custom_components.terralyra_ignis.const import DOMAIN
from custom_components.terralyra_ignis.inpe_map import get_inpe_map
from custom_components.terralyra_ignis.inpe_presentation import project_inpe
from custom_components.terralyra_ignis.derived_sources.inpe.coordinator import State
from custom_components.terralyra_ignis.derived_sources.inpe.centroids import Centroid

LOC = SimpleNamespace(id='acre', name='Acre', latitude=-9.9, longitude=-67.8, radius_km=100, enabled=True)
RECORD = Centroid(42, -67.8, -9.9, 'Vegetação', 'Ativo', 10, 2, 'AC', 'Rio Branco', ('AC',))
NOW = datetime(2026,10,20,tzinfo=UTC)


def test_projection_radius_disabled_locations_and_duplicate_locations():
    state=State('success',(RECORD,),NOW)
    assert len(project_inpe(state,(LOC,LOC)))==1
    assert project_inpe(state,(SimpleNamespace(**{**vars(LOC),'enabled':False}),))==()
    assert project_inpe(state,(SimpleNamespace(**{**vars(LOC),'latitude':0}),))==()
    assert project_inpe(State('error',(RECORD,),NOW), (LOC,))==()


async def test_success_empty_error_recovery_and_disable(hass):
    entry=MockConfigEntry(domain=DOMAIN,options={'inpe_enabled':True,'inpe_states':['AC']});entry.add_to_hass(hass)
    manager=get_inpe_map(hass,entry)
    component=EntityComponent(logging.getLogger(__name__),'geo_location',hass)
    with patch('custom_components.terralyra_ignis.inpe_map.resolve_monitored_locations',return_value=(LOC,)):
        manager.bind(lambda entities:hass.async_create_task(component.async_add_entities(entities)))
        await manager.set_enabled(True)
        for state, expected in [(State('success',(RECORD,),NOW),1), (State('success',(),NOW),0),
                                (State('success',(RECORD,),NOW),1), (State('error',(RECORD,),NOW,'retrieval_failed'),0),
                                (State('success',(RECORD,),NOW),1)]:
            manager.owner.state=state
            async_dispatcher_send(hass,f'{DOMAIN}_inpe_{entry.entry_id}')
            await hass.async_block_till_done()
            assert len(manager.entities)==expected
        entity=next(iter(manager.entities.values()))
        attrs=hass.states.get(entity.entity_id).attributes
        assert attrs['source']=='terralyra_ignis_inpe_reports'
        assert attrs['last_success_at']==NOW.isoformat()
        assert 'acquired' not in attrs
        assert attrs['coverage_complete'] is False
        await manager.close()
        await hass.async_block_till_done()
        assert not manager.entities
        assert manager._unsubscribe is None
        assert hass.states.get(entity.entity_id) is None


async def test_late_add_after_disable_and_excess_markers(hass):
    entry=MockConfigEntry(domain=DOMAIN,options={'inpe_enabled':True,'inpe_states':['AC']});entry.add_to_hass(hass)
    manager=get_inpe_map(hass,entry); queued=[]
    component=EntityComponent(logging.getLogger(__name__),'geo_location',hass)
    with patch('custom_components.terralyra_ignis.inpe_map.resolve_monitored_locations',return_value=(LOC,)):
        manager.owner.state=State('success',tuple(replace(RECORD,source_id=i) for i in range(501)),NOW)
        manager.bind(queued.extend)
        await manager.set_enabled(True)
        assert manager.status=='display_limit_exceeded' and not queued
        manager.owner.state=State('success',(RECORD,),NOW)
        await manager.set_enabled(True)
        assert len(queued)==1
        await manager.set_enabled(False)
        await component.async_add_entities(queued)
        await hass.async_block_till_done()
        assert not manager.entities
        await manager.close()
