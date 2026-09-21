"""HA-native Canada ownership stays inactive until an explicit caller uses it."""
from unittest.mock import AsyncMock, patch

from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import Store

from custom_components.terralyra_ignis.official_sources.canada.owner import get_canada_owner, STORE_KEY


async def test_owner_is_shared_and_construction_performs_no_io(hass):
    with patch.object(Store, 'async_load', new_callable=AsyncMock) as load, \
         patch.object(Store, 'async_save', new_callable=AsyncMock) as save:
        owner = get_canada_owner(hass)
        assert get_canada_owner(hass) is owner
        assert owner.session is async_get_clientsession(hass)
        assert owner.store.store.key == STORE_KEY
        load.assert_not_awaited()
        save.assert_not_awaited()


async def test_ha_storage_roundtrip_keeps_request_pause(hass, hass_storage):
    owner = get_canada_owner(hass)
    await owner.store.async_initialize(confirmed_new=True)
    owner.fetcher = AsyncMock(return_value=(
        {'type': 'FeatureCollection', 'features': [], 'numberMatched': 0,
         'numberReturned': 0}, {}))
    state = await owner.refresh()
    restored = await owner.store.async_load()
    assert restored.next_attempt == state.next_attempt
    await owner.refresh()
    owner.fetcher.assert_awaited_once()
    assert not owner.session.closed
