"""Lazy shared NIFC ownership with no default network or storage activity."""
import asyncio
from unittest.mock import AsyncMock, patch

from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import Store
import pytest

from custom_components.terralyra_ignis.official_sources.nifc.owner import get_nifc_owner, STORE_KEY
from custom_components.terralyra_ignis.official_sources.nifc.query import FetchResult


async def test_single_owner_registration_performs_no_io(hass):
    with patch.object(Store,'async_load',new_callable=AsyncMock) as load, patch.object(Store,'async_save',new_callable=AsyncMock) as save:
        first=get_nifc_owner(hass)
        assert get_nifc_owner(hass) is first
        assert first.client._session is async_get_clientsession(hass)
        load.assert_not_awaited(); save.assert_not_awaited()
        assert first.state is None


@pytest.mark.parametrize('enabled,locations',[(False,False),(False,True),(True,False)])
async def test_ineligible_refresh_never_loads_or_fetches(hass,enabled,locations):
    owner=get_nifc_owner(hass)
    with patch.object(owner.coordinator,'setup',new_callable=AsyncMock) as setup:
        assert await owner.async_refresh(enabled=enabled,has_enabled_locations=locations)=='skipped'
        setup.assert_not_awaited()


async def test_two_callers_share_request_and_cooldown(hass,hass_storage):
    await Store(hass,1,STORE_KEY).async_save({'version':1,'wait_seconds':0,'failures':0})
    entered,release=asyncio.Event(),asyncio.Event()
    calls=[]
    async def fetch(self):
        calls.append(1); entered.set(); await release.wait()
        return FetchResult((),1,1,'terminal_reported')
    with patch('custom_components.terralyra_ignis.official_sources.nifc.owner.NifcClient.async_fetch',fetch):
        first=get_nifc_owner(hass); second=get_nifc_owner(hass)
        task=asyncio.create_task(first.async_refresh(enabled=True,has_enabled_locations=True))
        await entered.wait()
        assert await second.async_refresh(enabled=True,has_enabled_locations=True)=='skipped'
        release.set(); assert await task=='retrieved'
        assert await second.async_refresh(enabled=True,has_enabled_locations=True)=='skipped'
    assert len(calls)==1
    assert not async_get_clientsession(hass).closed


async def test_missing_state_blocks_without_implicit_initialization(hass,hass_storage):
    owner=get_nifc_owner(hass)
    with pytest.raises(ValueError):
        await owner.async_refresh(enabled=True,has_enabled_locations=True)
    assert owner.diagnostics()['problem']=='storage_load_failed'
    assert await Store(hass,1,STORE_KEY).async_load() is None
