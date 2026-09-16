"""First-use intent never doubles as a cooldown reset or history migration."""
from unittest.mock import AsyncMock, patch

from homeassistant.helpers.storage import Store
import pytest

from custom_components.terralyra_ignis.official_sources.nifc.owner import (
    get_nifc_owner, STORE_KEY, INITIALIZATION_KEY,
)


async def test_first_use_requires_explicit_confirmation(hass,hass_storage):
    owner=get_nifc_owner(hass)
    with pytest.raises(ValueError): await owner.async_initialize()
    assert await Store(hass,1,STORE_KEY).async_load() is None
    assert await Store(hass,1,INITIALIZATION_KEY).async_load() is None
    with patch.object(owner.client,'async_fetch',new_callable=AsyncMock) as fetch:
        assert await owner.async_initialize(confirmed_new=True)=='initialized'
        fetch.assert_not_awaited()
    assert await Store(hass,1,STORE_KEY).async_load()=={'version':1,'wait_seconds':0,'failures':0}
    assert await Store(hass,1,INITIALIZATION_KEY).async_load()=={'version':1,'phase':'ready'}


@pytest.mark.parametrize('wait',[7200,None])
async def test_existing_cooldown_is_never_reset(hass,hass_storage,wait):
    saved={'version':1,'wait_seconds':wait,'failures':3}
    await Store(hass,1,STORE_KEY).async_save(saved)
    assert await get_nifc_owner(hass).async_initialize(confirmed_new=True)=='existing'
    assert await Store(hass,1,STORE_KEY).async_load()==saved


async def test_missing_established_state_is_not_first_use(hass,hass_storage):
    await Store(hass,1,INITIALIZATION_KEY).async_save({'version':1,'phase':'ready'})
    with pytest.raises(ValueError): await get_nifc_owner(hass).async_initialize(confirmed_new=True)
    assert await Store(hass,1,STORE_KEY).async_load() is None


async def test_interrupted_initialization_keeps_review_marker(hass,hass_storage):
    owner=get_nifc_owner(hass)
    with patch.object(owner._store,'async_save',side_effect=OSError('disk failure')):
        with pytest.raises(OSError): await owner.async_initialize(confirmed_new=True)
    assert await Store(hass,1,INITIALIZATION_KEY).async_load()=={'version':1,'phase':'started'}
    with pytest.raises(ValueError): await owner.async_initialize(confirmed_new=True)


async def test_corrupt_cooldown_is_not_overwritten(hass,hass_storage):
    await Store(hass,1,STORE_KEY).async_save({'invalid':'preserve'})
    with pytest.raises(ValueError): await get_nifc_owner(hass).async_initialize(confirmed_new=True)
    assert await Store(hass,1,STORE_KEY).async_load()=={'invalid':'preserve'}
    assert await Store(hass,1,INITIALIZATION_KEY).async_load() is None


async def test_started_ledger_blocks_refresh_even_with_valid_checkpoint(hass,hass_storage):
    await Store(hass,1,INITIALIZATION_KEY).async_save({'version':1,'phase':'started'})
    await Store(hass,1,STORE_KEY).async_save({'version':1,'wait_seconds':0,'failures':0})
    owner=get_nifc_owner(hass)
    with patch.object(owner.coordinator,'setup',new_callable=AsyncMock) as setup:
        with pytest.raises(ValueError):
            await owner.async_refresh(enabled=True,has_enabled_locations=True)
        setup.assert_not_awaited()

    assert owner.diagnostics()['problem'] == 'review_required'
    assert owner.diagnostics()['in_flight'] is False


async def test_ledger_load_failure_is_visible_and_retry_clears_it(hass, hass_storage):
    owner = get_nifc_owner(hass)
    with patch.object(owner._initialization_store, 'async_load', side_effect=OSError('private path')):
        with pytest.raises(OSError):
            await owner.async_refresh(enabled=True, has_enabled_locations=True)
    assert owner.diagnostics()['problem'] == 'storage_load_failed'
    assert 'private path' not in str(owner.diagnostics())
    await owner.async_initialize(confirmed_new=True)
    # Keep a real future cooldown so this diagnostic retry performs no request.
    await owner._store.async_save({'version': 1, 'wait_seconds': 7200, 'failures': 0})
    with patch.object(owner.client, 'async_fetch', new_callable=AsyncMock) as fetch:
        assert await owner.async_refresh(enabled=True, has_enabled_locations=True) == 'skipped'
        fetch.assert_not_awaited()
    assert owner.diagnostics()['problem'] is None


async def test_ledger_read_counts_as_in_flight(hass, hass_storage):
    owner = get_nifc_owner(hass)
    async def load():
        assert owner.diagnostics()['in_flight'] is True
        return {'version': 1, 'phase': 'started'}
    with patch.object(owner._initialization_store, 'async_load', side_effect=load):
        with pytest.raises(ValueError):
            await owner.async_refresh(enabled=True, has_enabled_locations=True)
    assert owner.diagnostics()['in_flight'] is False
