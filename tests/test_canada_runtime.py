"""Canada opt-in lifecycle and shared request ownership."""
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch
from homeassistant.helpers.storage import Store
from pytest_homeassistant_custom_component.common import MockConfigEntry
from custom_components.terralyra_ignis.const import DOMAIN
from custom_components.terralyra_ignis.canada_runtime import get_canada_runtime
from custom_components.terralyra_ignis.canada_sensor import CanadaDiagnosticSensor
from custom_components.terralyra_ignis.official_sources.canada.owner import STORE_KEY

EMPTY = ({'type': 'FeatureCollection', 'features': [], 'numberMatched': 0, 'numberReturned': 0}, {})
LOCATIONS = 'custom_components.terralyra_ignis.canada_runtime.resolve_monitored_locations'


def entry(hass):
    selected = MockConfigEntry(domain=DOMAIN)
    selected.add_to_hass(hass)
    return selected


async def test_sensor_is_disabled_and_inert_before_added(hass):
    runtime = get_canada_runtime(hass)
    sensor = CanadaDiagnosticSensor(entry(hass), runtime.owner)
    with patch.object(runtime.owner, 'async_refresh', new_callable=AsyncMock) as refresh:
        await sensor.async_update()
        assert sensor.entity_registry_enabled_default is False
        assert sensor.native_value == 'not_requested'
        assert not sensor.extra_state_attributes['retrieval_enabled']
        refresh.assert_not_awaited()
    await runtime.async_stop()


async def test_missing_initialization_can_be_initialized_without_reset(hass, hass_storage):
    runtime = get_canada_runtime(hass)
    selected = entry(hass)
    runtime.owner.fetcher = AsyncMock(return_value=EMPTY)
    with patch(LOCATIONS, return_value=[SimpleNamespace(enabled=True)]):
        runtime.attach(selected, Mock())
        await runtime._task
        assert runtime.owner.initialization_status == 'required'
        assert not runtime.owner.store.blocked
        assert await Store(hass, 1, STORE_KEY).async_load() is None
        runtime.owner.fetcher.assert_not_awaited()
        await runtime.owner.async_initialize(confirmed_new=True)
        runtime.request_refresh()
        await runtime._task
        assert runtime.owner.state.status == 'available'
        runtime.owner.fetcher.assert_awaited_once()
        await runtime.detach(selected)


async def test_two_entries_share_one_request_and_manual_refresh_respects_pause(hass, hass_storage):
    runtime = get_canada_runtime(hass)
    await runtime.owner.async_initialize(confirmed_new=True)
    entered, release = asyncio.Event(), asyncio.Event()
    async def fetch(session):
        entered.set()
        await release.wait()
        return EMPTY
    runtime.owner.fetcher = AsyncMock(side_effect=fetch)
    one, two = entry(hass), entry(hass)
    with patch(LOCATIONS, return_value=[SimpleNamespace(enabled=True)]):
        runtime.attach(one, Mock())
        runtime.attach(two, Mock())
        await entered.wait()
        task = runtime._task
        runtime.request_refresh()
        assert runtime._task is task
        await runtime.detach(one)
        assert not task.cancelled()
        release.set()
        await task
        runtime.request_refresh()
        await runtime._task
        runtime.owner.fetcher.assert_awaited_once()
        await runtime.detach(two)
        assert runtime._timer is None


async def test_no_locations_and_shutdown_never_fetch(hass):
    runtime = get_canada_runtime(hass)
    selected = entry(hass)
    runtime.owner.fetcher = AsyncMock()
    with patch(LOCATIONS, return_value=[]):
        runtime.attach(selected, Mock())
        assert runtime._task is None
        await runtime.async_stop()
        runtime.request_refresh()
        assert runtime._timer is None
        runtime.owner.fetcher.assert_not_awaited()
        await runtime.detach(selected)
