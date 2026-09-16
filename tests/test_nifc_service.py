"""Real service dispatch and isolated HA storage for explicit first-use intent."""
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
import voluptuous as vol
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import Context
from homeassistant.exceptions import ServiceValidationError, Unauthorized
from homeassistant.helpers.storage import Store
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.terralyra_ignis.const import DOMAIN
from custom_components.terralyra_ignis.nifc_service import register_nifc_initialization
from custom_components.terralyra_ignis.official_sources.nifc.owner import get_nifc_owner, STORE_KEY


@pytest.fixture
def action(hass):
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)
    entry.mock_state(hass, ConfigEntryState.LOADED)
    register_nifc_initialization(hass)
    return {'config_entry_id': entry.entry_id, 'confirm_first_use': True}


async def call(hass, data, user_id='admin'):
    return await hass.services.async_call(DOMAIN, 'initialize_nifc', data,
        context=Context(user_id=user_id), blocking=True, return_response=True)


async def test_admin_initialization_and_repeat_preserve_history_and_wait(hass, hass_storage, action):
    history = Store(hass, 1, 'synthetic_incident_history')
    await history.async_save({'incidents': ['preserve']})
    owner = get_nifc_owner(hass)
    with patch.object(hass.auth, 'async_get_user', AsyncMock(return_value=SimpleNamespace(is_admin=True))), patch.object(owner.client, 'async_fetch', new_callable=AsyncMock) as fetch:
        assert await call(hass, action) == {'status': 'initialized', 'retrieval_enabled': False, 'history_changed': False}
        saved = {'version': 1, 'wait_seconds': 7200, 'failures': 2}
        await Store(hass, 1, STORE_KEY).async_save(saved)
        assert (await call(hass, action))['status'] == 'existing'
        assert await Store(hass, 1, STORE_KEY).async_load() == saved
        fetch.assert_not_awaited()
    assert await history.async_load() == {'incidents': ['preserve']}


@pytest.mark.parametrize('user_id,admin', [('normal', False), (None, True)])
async def test_no_user_or_non_admin_cannot_initialize(hass, action, user_id, admin):
    owner = get_nifc_owner(hass)
    with patch.object(hass.auth, 'async_get_user', AsyncMock(return_value=SimpleNamespace(is_admin=admin))), patch.object(owner, 'async_initialize', new_callable=AsyncMock) as initialize:
        with pytest.raises(Unauthorized):
            await call(hass, action, user_id)
        initialize.assert_not_awaited()


@pytest.mark.parametrize('confirmation', [False, 'true', 1, None])
async def test_strict_confirmation(hass, action, confirmation):
    with pytest.raises(vol.Invalid):
        await call(hass, action | {'confirm_first_use': confirmation})


async def test_bad_entry_and_storage_failure(hass, action):
    owner = get_nifc_owner(hass)
    with patch.object(hass.auth, 'async_get_user', AsyncMock(return_value=SimpleNamespace(is_admin=True))), patch.object(owner, 'async_initialize', new_callable=AsyncMock) as initialize:
        with pytest.raises(ServiceValidationError):
            await call(hass, action | {'config_entry_id': 'missing'})
        initialize.assert_not_awaited()
        initialize.side_effect = OSError('private disk path')
        with pytest.raises(ServiceValidationError) as error:
            await call(hass, action)
        assert 'private disk path' not in str(error.value)


async def test_unloaded_entry_and_missing_confirmation(hass, action):
    with pytest.raises(vol.Invalid):
        await call(hass, {'config_entry_id': action['config_entry_id']})
    entry = hass.config_entries.async_get_entry(action['config_entry_id'])
    entry.mock_state(hass, ConfigEntryState.NOT_LOADED)
    owner = get_nifc_owner(hass)
    with patch.object(hass.auth, 'async_get_user', AsyncMock(return_value=SimpleNamespace(is_admin=True))), patch.object(owner, 'async_initialize', new_callable=AsyncMock) as initialize:
        with pytest.raises(ServiceValidationError):
            await call(hass, action)
        initialize.assert_not_awaited()


async def test_recovery_action_is_explicit_and_preserves_server_wait(hass,hass_storage,action):
    owner=get_nifc_owner(hass)
    await owner.async_initialize(confirmed_new=True)
    await owner._store.async_save({'version':2,'wait_seconds':None,'failures':1,'resume_wait_seconds':7200})
    data={'config_entry_id':action['config_entry_id'],'confirm_review':True}
    with patch.object(hass.auth,'async_get_user',AsyncMock(return_value=SimpleNamespace(is_admin=True))):
        result=await hass.services.async_call(DOMAIN,'recover_nifc',data,
            context=Context(user_id='admin'),blocking=True,return_response=True)
    assert result['status']=='recovered'
    assert result['retrieval_enabled'] is False
    assert (await owner._store.async_load())['wait_seconds'] >= 7199


async def test_recovery_cannot_reset_unknown_pause(hass,hass_storage,action):
    owner=get_nifc_owner(hass)
    await owner.async_initialize(confirmed_new=True)
    saved={'version':1,'wait_seconds':None,'failures':1}
    await owner._store.async_save(saved)
    with patch.object(hass.auth,'async_get_user',AsyncMock(return_value=SimpleNamespace(is_admin=True))):
        with pytest.raises(ServiceValidationError):
            await hass.services.async_call(DOMAIN,'recover_nifc',
                {'config_entry_id':action['config_entry_id'],'confirm_review':True},
                context=Context(user_id='admin'),blocking=True,return_response=True)
    assert await owner._store.async_load()==saved
