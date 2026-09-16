"""Shared HA listener lifecycle, durable cooldown and scoped Repair behavior."""
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.storage import Store
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.terralyra_ignis.const import DOMAIN
from custom_components.terralyra_ignis.nifc_runtime import get_nifc_runtime
from custom_components.terralyra_ignis.official_sources.nifc.owner import STORE_KEY
from custom_components.terralyra_ignis.official_sources.nifc.query import FetchResult


def entry(hass):
    result=MockConfigEntry(domain=DOMAIN)
    result.add_to_hass(hass)
    result.mock_state(hass,ConfigEntryState.LOADED)
    return result


async def test_two_enabled_entries_share_fetch_manual_refresh_and_unload(hass,hass_storage):
    first,second=entry(hass),entry(hass)
    started,release=asyncio.Event(),asyncio.Event()
    calls=[]
    async def fetch(self,**kwargs):
        calls.append(1)
        assert kwargs['inventory'] is True
        started.set();await release.wait()
        return FetchResult((),2,1,'terminal_reported',retrieval_method='verified_id_inventory')
    with patch('custom_components.terralyra_ignis.official_sources.nifc.owner.NifcClient.async_fetch',fetch), patch('custom_components.terralyra_ignis.nifc_runtime.resolve_monitored_locations',return_value=[SimpleNamespace(enabled=True)]):
        runtime=get_nifc_runtime(hass)
        await runtime.owner.async_initialize(confirmed_new=True)
        one,two=Mock(),Mock()
        runtime.attach(first,one);runtime.attach(second,two)
        await started.wait();task=runtime._task
        runtime.request_refresh();assert runtime._task is task
        await runtime.detach(first);assert not task.cancelled()
        release.set();await task;await asyncio.sleep(0)
        assert two.called
        runtime.request_refresh();await runtime._task
        assert runtime.owner.state.last_success is not None
        assert runtime.owner.state.failures == 0
        assert len(calls) == 1
        await runtime.detach(second)
        assert runtime._timer is None
        assert not runtime._listeners


async def test_disabled_or_no_enabled_locations_never_read_storage(hass):
    runtime=get_nifc_runtime(hass)
    with patch.object(runtime.owner,'async_refresh',new_callable=AsyncMock) as refresh, patch('custom_components.terralyra_ignis.nifc_runtime.resolve_monitored_locations',return_value=[]):
        runtime.request_refresh();assert runtime._task is None
        selected=entry(hass);runtime.attach(selected,Mock());assert runtime._task is None
        refresh.assert_not_awaited()
        await runtime.detach(selected)


async def test_fresh_install_waits_for_explicit_initialization(hass,hass_storage):
    runtime=get_nifc_runtime(hass);selected=entry(hass)
    with patch('custom_components.terralyra_ignis.nifc_runtime.resolve_monitored_locations',return_value=[SimpleNamespace(enabled=True)]):
        runtime.attach(selected,Mock());await runtime._task
        assert runtime.owner.initialization_status == 'required'
        assert await Store(hass,1,STORE_KEY).async_load() is None
        assert ir.async_get(hass).async_get_issue(DOMAIN,f'{selected.entry_id}_nifc_research') is None
        await runtime.detach(selected)


async def test_last_unload_cancels_fetch_and_preserves_pause_and_history(hass,hass_storage):
    started=asyncio.Event()
    async def fetch(self,**kwargs):
        started.set();await asyncio.Future()
    history=Store(hass,1,'synthetic_nifc_history')
    await history.async_save({'events':['keep']})
    with patch('custom_components.terralyra_ignis.official_sources.nifc.owner.NifcClient.async_fetch',fetch), patch('custom_components.terralyra_ignis.nifc_runtime.resolve_monitored_locations',return_value=[SimpleNamespace(enabled=True)]):
        runtime=get_nifc_runtime(hass);await runtime.owner.async_initialize(confirmed_new=True)
        selected=entry(hass);runtime.attach(selected,Mock());await started.wait()
        await runtime.detach(selected)
        assert runtime._task.done()
        assert (await Store(hass,1,STORE_KEY).async_load())['wait_seconds'] is None
        await runtime.owner.async_recover()
        assert (await Store(hass,1,STORE_KEY).async_load())['wait_seconds'] >= 899
        assert await history.async_load()=={'events':['keep']}


async def test_repair_is_scoped_and_cleared_by_disable(hass,hass_storage):
    runtime=get_nifc_runtime(hass);selected=entry(hass)
    await runtime.owner._initialization_store.async_save({'version':1,'phase':'started'})
    with patch('custom_components.terralyra_ignis.nifc_runtime.resolve_monitored_locations',return_value=[SimpleNamespace(enabled=True)]):
        runtime.attach(selected,Mock());await runtime._task;await asyncio.sleep(0)
        issue=ir.async_get(hass).async_get_issue(DOMAIN,f'{selected.entry_id}_nifc_research')
        assert issue.translation_key=='nifc_review_required'
        await runtime.detach(selected)
        assert ir.async_get(hass).async_get_issue(DOMAIN,f'{selected.entry_id}_nifc_research') is None


async def test_shutdown_stops_scheduler(hass,hass_storage):
    runtime=get_nifc_runtime(hass);selected=entry(hass)
    with patch('custom_components.terralyra_ignis.nifc_runtime.resolve_monitored_locations',return_value=[]):
        runtime.attach(selected,Mock())
        await runtime.async_stop()
        runtime.request_refresh()
        assert runtime._task is None
        assert runtime._timer is None
        await runtime.detach(selected)


async def test_slow_storage_is_owned_after_unload_and_blocks_recovery(hass,hass_storage):
    runtime=get_nifc_runtime(hass)
    await runtime.owner.async_initialize(confirmed_new=True)
    guarded=runtime.owner._store
    guarded._timeout=0.01
    entered,release=asyncio.Event(),asyncio.Event()
    raw_save=guarded._store.async_save
    async def slow_save(data):
        entered.set();await release.wait();await raw_save(data)
    selected=entry(hass)
    with patch.object(guarded._store,'async_save',side_effect=slow_save), patch('custom_components.terralyra_ignis.nifc_runtime.resolve_monitored_locations',return_value=[SimpleNamespace(enabled=True)]):
        runtime.attach(selected,Mock())
        await entered.wait();await runtime._task
        try:
            assert guarded.pending
            assert runtime.owner.diagnostics()['storage_review_required']
            await runtime.detach(selected)
            with pytest.raises(OSError):await runtime.owner.async_recover()
            assert guarded.pending
        finally:
            release.set();await guarded._pending
    await runtime.owner.async_recover()
    assert not guarded.blocked
    assert (await guarded.async_load())['wait_seconds'] >= 899


async def test_reload_restores_server_wait_without_request(hass,hass_storage):
    from custom_components.terralyra_ignis.official_sources.nifc.owner import NifcOwner, INITIALIZATION_KEY
    from custom_components.terralyra_ignis.official_sources.nifc.errors import SourceHTTPError
    with patch('custom_components.terralyra_ignis.official_sources.nifc.owner.NifcClient.async_fetch',side_effect=SourceHTTPError(429,'7200')) as fetch:
        runtime=get_nifc_runtime(hass);await runtime.owner.async_initialize(confirmed_new=True)
        assert await runtime.owner.async_refresh(enabled=True,has_enabled_locations=True)=='failed'
        fetch.assert_awaited_once()
    restarted=NifcOwner(None,Store(hass,1,STORE_KEY),Store(hass,1,INITIALIZATION_KEY))
    assert await restarted.async_refresh(enabled=True,has_enabled_locations=True)=='skipped'
    assert restarted.state.failures==1
    assert restarted.state.last_success is None
