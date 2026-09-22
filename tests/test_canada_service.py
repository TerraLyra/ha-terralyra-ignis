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
from custom_components.terralyra_ignis.canada_service import register_canada_initialization
from custom_components.terralyra_ignis.official_sources.canada.owner import get_canada_owner, STORE_KEY


@pytest.fixture
def action(hass):
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)
    entry.mock_state(hass, ConfigEntryState.LOADED)
    register_canada_initialization(hass)
    return {'config_entry_id': entry.entry_id, 'confirm_first_use': True}


async def call(hass, data, user_id='admin'):
    return await hass.services.async_call(DOMAIN, 'initialize_canada', data,
        context=Context(user_id=user_id), blocking=True, return_response=True)


async def test_admin_initialization_and_repeat_preserve_history_and_wait(hass, hass_storage, action):
    history = Store(hass, 1, 'synthetic_incident_history')
    await history.async_save({'incidents': ['preserve']})
    owner = get_canada_owner(hass)
    with patch.object(hass.auth, 'async_get_user', AsyncMock(return_value=SimpleNamespace(is_admin=True))), patch.object(owner, 'fetcher', new_callable=AsyncMock) as fetch:
        assert await call(hass, action) == {'status': 'initialized', 'retrieval_enabled': False, 'history_changed': False}
        saved = await Store(hass, 1, STORE_KEY).async_load()
        await Store(hass, 1, STORE_KEY).async_save(saved)
        assert (await call(hass, action))['status'] == 'existing'
        assert await Store(hass, 1, STORE_KEY).async_load() == saved
        fetch.assert_not_awaited()
    assert await history.async_load() == {'incidents': ['preserve']}


@pytest.mark.parametrize('user_id,admin', [('normal', False), (None, True)])
async def test_no_user_or_non_admin_cannot_initialize(hass, action, user_id, admin):
    owner = get_canada_owner(hass)
    with patch.object(hass.auth, 'async_get_user', AsyncMock(return_value=SimpleNamespace(is_admin=admin))), patch.object(owner, 'async_initialize', new_callable=AsyncMock) as initialize:
        with pytest.raises(Unauthorized):
            await call(hass, action, user_id)
        initialize.assert_not_awaited()


@pytest.mark.parametrize('confirmation', [False, 'true', 1, None])
async def test_strict_confirmation(hass, action, confirmation):
    with pytest.raises(vol.Invalid):
        await call(hass, action | {'confirm_first_use': confirmation})


async def test_bad_entry_and_storage_failure(hass, action):
    owner = get_canada_owner(hass)
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
    owner = get_canada_owner(hass)
    with patch.object(hass.auth, 'async_get_user', AsyncMock(return_value=SimpleNamespace(is_admin=True))), patch.object(owner, 'async_initialize', new_callable=AsyncMock) as initialize:
        with pytest.raises(ServiceValidationError):
            await call(hass, action)
        initialize.assert_not_awaited()



async def test_recovery_action_preserves_wait_and_never_fetches(hass, hass_storage, action):
    from datetime import timedelta
    from custom_components.terralyra_ignis.official_sources.canada.retry import RefreshState
    owner = get_canada_owner(hass)
    await owner.async_initialize(confirmed_new=True)
    state = RefreshState(status='review_required', review_required=True,
                         next_attempt=owner.clock() + timedelta(days=2))
    await owner.store.async_save(state)
    with patch.object(hass.auth, 'async_get_user', AsyncMock(return_value=SimpleNamespace(is_admin=True))), patch.object(owner, 'fetcher', new_callable=AsyncMock) as fetch:
        result = await hass.services.async_call(DOMAIN, 'recover_canada',
            {'config_entry_id': action['config_entry_id'], 'confirm_review': True},
            context=Context(user_id='admin'), blocking=True, return_response=True)
        assert result == {'status': 'recovered', 'retrieval_enabled': False, 'history_changed': False}
        fetch.assert_not_awaited()
    restored = await owner.store.async_load()
    assert restored.next_attempt == state.next_attempt
    assert not restored.review_required
