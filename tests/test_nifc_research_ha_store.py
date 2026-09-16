"""Actual HA Store API with isolated pytest storage; no runtime NIFC activation."""
from importlib import import_module
from pathlib import Path
from unittest.mock import AsyncMock

from homeassistant.helpers.storage import Store
import pytest

KEY = 'terralyra_ignis.test_only_nifc_cooldown'


@pytest.fixture
def research(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / 'tools' / 'source_research'))
    return (import_module('nifc_async_storage').AsyncStoredResearchCoordinator,
            import_module('nifc_fetch').FetchResult)


async def test_real_store_save_reload_and_history_isolation(hass, hass_storage, research):
    coordinator_type, result_type = research
    # Pytest's isolated storage backend; use the real HA Store implementation.
    history = Store(hass, 1, 'terralyra_ignis.test_only_history')
    await history.async_save({'events': ['retained synthetic event']})
    store = Store(hass, 1, KEY)
    await store.async_save({'version': 1, 'wait_seconds': 0, 'failures': 0})
    fetch = AsyncMock(return_value=result_type((), 1, 1, 'terminal_reported'))
    first = coordinator_type(store, fetcher=fetch, clock=lambda: 100)
    await first.setup()
    assert await first.refresh(enabled=True) == 'retrieved'
    saved = await Store(hass, 1, KEY).async_load()
    assert saved == {'version': 1, 'wait_seconds': 900, 'failures': 0}
    restored = coordinator_type(Store(hass, 1, KEY), fetcher=fetch, clock=lambda: 5)
    await restored.setup()
    assert await restored.refresh(enabled=True) == 'skipped'
    fetch.assert_awaited_once()
    assert await Store(hass, 1, 'terralyra_ignis.test_only_history').async_load() == {
        'events': ['retained synthetic event']}


async def test_real_store_missing_data_does_not_start_network(hass, hass_storage, research):
    coordinator_type, _ = research
    fetch = AsyncMock()
    coordinator = coordinator_type(Store(hass, 1, KEY), fetcher=fetch)
    with pytest.raises(ValueError):
        await coordinator.setup()
    fetch.assert_not_awaited()
    assert coordinator.diagnostics()['problem'] == 'storage_load_failed'
    assert await Store(hass, 1, KEY).async_load() is None


async def test_real_store_manual_pause_survives_new_instance(hass, hass_storage, research):
    coordinator_type, _ = research
    store = Store(hass, 1, KEY)
    await store.async_save({'version': 1, 'wait_seconds': None, 'failures': 2})
    fetch = AsyncMock()
    coordinator = coordinator_type(Store(hass, 1, KEY), fetcher=fetch)
    await coordinator.setup()
    assert await coordinator.refresh(enabled=True) == 'skipped'
    assert coordinator.diagnostics()['problem'] == 'review_required'
    fetch.assert_not_awaited()
