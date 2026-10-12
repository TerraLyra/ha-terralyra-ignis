"""Admin service and storage recovery acceptance with real HA dispatch."""
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from datetime import datetime, UTC, timedelta
import pytest
import voluptuous as vol
from homeassistant.core import Context
from homeassistant.config_entries import ConfigEntryState
from homeassistant.exceptions import Unauthorized, ServiceValidationError
from pytest_homeassistant_custom_component.common import MockConfigEntry
from custom_components.terralyra_ignis.const import DOMAIN
from custom_components.terralyra_ignis.tasalert_service import register_tasalert_initialization
from custom_components.terralyra_ignis.tasalert_runtime import get_tasalert_runtime


@pytest.fixture
def action(hass):
    entry=MockConfigEntry(domain=DOMAIN);entry.add_to_hass(hass)
    entry.mock_state(hass,ConfigEntryState.LOADED)
    register_tasalert_initialization(hass)
    return {'config_entry_id':entry.entry_id,'confirm_first_use':True}


async def call(hass,data,user_id='admin',service='initialize_tasalert'):
    return await hass.services.async_call(DOMAIN,service,data,context=Context(user_id=user_id),blocking=True,return_response=True)


async def test_initialize_repeat_and_recover_never_fetch_or_erase(hass,hass_storage,action):
    runtime=get_tasalert_runtime(hass);owner=runtime.owner
    with patch.object(hass.auth,'async_get_user',AsyncMock(return_value=SimpleNamespace(is_admin=True))), patch.object(owner,'fetcher',new_callable=AsyncMock) as fetch:
        assert (await call(hass,action))['retrieval_enabled'] is False
        saved=await owner.store.async_load()
        await call(hass,action)
        assert saved==await owner.store.async_load()
        owner.blocked=True
        result=await call(hass,{'config_entry_id':action['config_entry_id'],'confirm_review':True},service='recover_tasalert')
        assert result['status']=='recovered'
        assert not owner.blocked
        assert owner.state.response.next_attempt>=datetime.now(UTC)+timedelta(minutes=29)
        fetch.assert_not_awaited()
    await runtime.async_stop()


@pytest.mark.parametrize('user_id,admin',[(None,True),('normal',False)])
async def test_unauthorized(hass,action,user_id,admin):
    with patch.object(hass.auth,'async_get_user',AsyncMock(return_value=SimpleNamespace(is_admin=admin))):
        with pytest.raises(Unauthorized):await call(hass,action,user_id)


@pytest.mark.parametrize('confirmation',[False,'true',1,None])
async def test_strict_confirmation(hass,action,confirmation):
    with pytest.raises(vol.Invalid):await call(hass,action|{'confirm_first_use':confirmation})


async def test_recovery_refuses_corrupt_and_missing_data(hass,hass_storage,action):
    runtime=get_tasalert_runtime(hass);owner=runtime.owner
    data={'config_entry_id':action['config_entry_id'],'confirm_review':True}
    with patch.object(hass.auth,'async_get_user',AsyncMock(return_value=SimpleNamespace(is_admin=True))):
        with pytest.raises(ServiceValidationError):await call(hass,data,service='recover_tasalert')
        await owner.store.async_save({'version':999})
        with pytest.raises(ServiceValidationError):await call(hass,data,service='recover_tasalert')
        assert await owner.store.async_load()=={'version':999}
        assert owner.blocked
    await runtime.async_stop()
