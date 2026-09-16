"""Actual entity registration preserves independent NIFC opt-in choices."""
from datetime import timedelta
import logging
from unittest.mock import AsyncMock, Mock, patch

from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import EntityPlatform
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.terralyra_ignis.nifc_calendar import NifcCalendar
from custom_components.terralyra_ignis.nifc_runtime import get_nifc_runtime
from custom_components.terralyra_ignis.switch import NifcMapSwitch


def platform(hass,entry,domain):
    result=EntityPlatform(hass=hass,logger=logging.getLogger(__name__),domain=domain,
        platform_name='terralyra_ignis',platform=None,scan_interval=timedelta(seconds=30),entity_namespace=None)
    result.config_entry=entry
    return result


async def test_calendar_default_disabled_and_independent_listener(hass):
    entry=MockConfigEntry(domain='terralyra_ignis');entry.add_to_hass(hass)
    runtime=get_nifc_runtime(hass)
    entity=NifcCalendar(hass,entry)
    entity_platform=platform(hass,entry,'calendar')
    with patch.object(runtime,'request_refresh') as refresh:
        await entity_platform.async_add_entities([entity])
        refresh.assert_not_called()
        registry=er.async_get(hass)
        entity_id=registry.async_get_entity_id('calendar','terralyra_ignis',entity.unique_id)
        assert registry.async_get(entity_id).disabled_by==er.RegistryEntryDisabler.INTEGRATION
        registry.async_update_entity(entity_id,disabled_by=None)
        runtime.attach(entry,Mock())
        entity=NifcCalendar(hass,entry)
        await entity_platform.async_add_entities([entity])
        assert (entry.entry_id,'calendar') in runtime._listeners
        assert (entry.entry_id,'diagnostic') in runtime._listeners
        await entity_platform.async_remove_entity(entity.entity_id)
        assert (entry.entry_id,'calendar') not in runtime._listeners
        assert (entry.entry_id,'diagnostic') in runtime._listeners
        await runtime.detach(entry)


async def test_map_switch_starts_off_and_subscribes_only_when_on(hass):
    entry=MockConfigEntry(domain='terralyra_ignis');entry.add_to_hass(hass)
    entity=NifcMapSwitch(hass,entry)
    runtime=entity._manager.runtime
    entity_platform=platform(hass,entry,'switch')
    with patch.object(runtime,'request_refresh'), patch.object(entity,'async_get_last_state',AsyncMock(return_value=None)):
        await entity_platform.async_add_entities([entity])
        assert entity.is_on is False
        assert (entry.entry_id,'map') not in runtime._listeners
        await entity.async_turn_on()
        assert (entry.entry_id,'map') in runtime._listeners
        await entity.async_turn_off()
        assert (entry.entry_id,'map') not in runtime._listeners
        await entity_platform.async_remove_entity(entity.entity_id)
        assert entity._manager._control_listener is None
