"""Isolated shared runtime and opt-in boundaries."""
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch
from homeassistant.helpers.storage import Store
from custom_components.terralyra_ignis.official_sources.tasalert.owner import TasAlertOwner
from custom_components.terralyra_ignis.tasalert_runtime import TasAlertRuntime
from custom_components.terralyra_ignis.tasalert_sensor import TasAlertDiagnosticSensor


async def test_disabled_sensor_is_inert(hass):
    owner=TasAlertOwner(Store(hass,1,'tasalert_test'),None)
    runtime=TasAlertRuntime(hass,owner)
    entry=SimpleNamespace(entry_id='one')
    sensor=TasAlertDiagnosticSensor(entry,runtime)
    owner.async_refresh=AsyncMock()
    await sensor.async_update()
    owner.async_refresh.assert_not_awaited()
    assert sensor.entity_registry_enabled_default is False
    assert sensor.native_value=='not_requested'
    await runtime.async_stop()


async def test_shared_runtime_initialization_and_detach(hass,hass_storage):
    owner=TasAlertOwner(Store(hass,1,'tasalert_runtime_test'),None)
    runtime=TasAlertRuntime(hass,owner)
    one=SimpleNamespace(entry_id='one');two=SimpleNamespace(entry_id='two')
    with patch('custom_components.terralyra_ignis.tasalert_runtime.resolve_monitored_locations',return_value=[SimpleNamespace(enabled=True)]):
        runtime.attach(one,Mock());await runtime.task
        assert owner.initialization_required
        assert not owner.blocked
        await owner.async_load(confirmed_new=True)
        owner.async_refresh=AsyncMock()
        runtime.attach(two,Mock());await runtime.task
        owner.async_refresh.assert_awaited_once()
        await runtime.detach(one)
        assert runtime.timer is not None
        await runtime.detach(two)
        assert runtime.timer is None
        runtime.request_refresh()
        assert owner.async_refresh.await_count==1
    await runtime.async_stop()


async def test_map_and_diagnostic_consumers_do_not_replace_each_other(hass):
    owner=TasAlertOwner(Store(hass,1,'tasalert_consumers'),None)
    runtime=TasAlertRuntime(hass,owner)
    owner.state=object();owner.async_refresh=AsyncMock()
    entry=SimpleNamespace(entry_id='one')
    with patch('custom_components.terralyra_ignis.tasalert_runtime.resolve_monitored_locations',return_value=[SimpleNamespace(enabled=True)]):
        runtime.attach(entry,Mock(),consumer='map')
        runtime.attach(entry,Mock())
        await runtime.task
        assert len(runtime.listeners)==2
        await runtime.detach(entry,consumer='map')
        assert runtime.enabled
        await runtime.detach(entry)
        assert not runtime.enabled
        assert runtime.timer is None
    await runtime.async_stop()
