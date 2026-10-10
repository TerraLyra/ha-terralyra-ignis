"""Bundled resources serve exact public files without long-lived caching."""
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.setup import async_setup_component

from custom_components.terralyra_ignis.frontend_resources import (
    CARD_FILES, URL_BASE, async_register_card_paths,
)


async def test_card_paths_served_once(hass, hass_client):
    assert await async_setup_component(hass, "http", {})
    await async_register_card_paths(hass)
    await async_register_card_paths(hass)
    client = await hass_client()
    for name in CARD_FILES:
        response = await client.get(f"{URL_BASE}/{name}")
        assert response.status == 200
        expected = Path("custom_components/terralyra_ignis/www") / name
        assert await response.read() == expected.read_bytes()
        assert "max-age=" not in response.headers.get("Cache-Control", "")
    response = await client.get(f"{URL_BASE}/manifest.json")
    assert response.status == 404


async def test_registration_failure_can_retry(hass):
    assert await async_setup_component(hass, "http", {})
    with patch.object(hass.http, "async_register_static_paths", new_callable=AsyncMock) as register:
        register.side_effect = [RuntimeError("temporary"), None]
        with pytest.raises(RuntimeError):
            await async_register_card_paths(hass)
        await async_register_card_paths(hass)
        await async_register_card_paths(hass)
        assert register.await_count == 2


async def test_registered_resources_resolve_to_bundled_files(hass, hass_client, hass_storage):
    """Exercise setup, concurrent registration and HTTP delivery together."""
    import asyncio
    from types import SimpleNamespace
    from homeassistant.core import Context
    from homeassistant.components.lovelace.const import LOVELACE_DATA
    from homeassistant.components.lovelace.resources import ResourceStorageCollection
    from custom_components.terralyra_ignis import async_setup
    from custom_components.terralyra_ignis.card_resource_plan import CARDS

    assert await async_setup_component(hass, 'http', {})
    collection = ResourceStorageCollection(
        hass, SimpleNamespace(async_load=AsyncMock(return_value={})))
    hass.data[LOVELACE_DATA] = SimpleNamespace(
        resources=collection, resource_mode='storage')
    assert await async_setup(hass, {})
    client = await hass_client()
    with patch.object(hass.auth, 'async_get_user', AsyncMock(
        return_value=SimpleNamespace(is_admin=True)
    )):
        async def register(card):
            return await hass.services.async_call(
                'terralyra_ignis', 'register_dashboard_card',
                {'card': card, 'confirm_no_renamed_copy': True},
                blocking=True, return_response=True, context=Context(user_id='admin'))
        for card, filename in CARDS.items():
            results = await asyncio.gather(register(card), register(card))
            assert sorted(result['status'] for result in results) == [
                'already_registered', 'registered']
            assert sum(result['changed'] for result in results) == 1
            for query in ('', '?v=first-install'):
                response = await client.get(results[0]['url'] + query)
                assert response.status == 200
                assert await response.read() == (
                    Path('custom_components/terralyra_ignis/www') / filename).read_bytes()
        assert len(collection.async_items()) == len(CARDS)
