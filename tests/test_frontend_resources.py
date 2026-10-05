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
