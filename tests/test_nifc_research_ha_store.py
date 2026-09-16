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


def sync_repair(hass, coordinator, entry_id='test-nifc', *, enabled=True):
    """Test-only wiring; production setup still does not activate the source."""
    from types import SimpleNamespace
    from custom_components.terralyra_ignis.repairs import async_sync_nifc_research_issue
    async_sync_nifc_research_issue(
        hass, SimpleNamespace(entry_id=entry_id), enabled=enabled,
        problem=coordinator.diagnostics()['problem'],
    )


async def test_save_failure_stops_fetch_and_creates_scoped_repair(hass, hass_storage, research):
    from unittest.mock import patch
    from homeassistant.helpers import issue_registry as ir
    coordinator_type, _ = research
    store = Store(hass, 1, KEY)
    await store.async_save({'version': 1, 'wait_seconds': 0, 'failures': 0})
    fetch = AsyncMock()
    coordinator = coordinator_type(store, fetcher=fetch)
    await coordinator.setup()
    with patch.object(store, 'async_save', side_effect=OSError('synthetic private path')):
        with pytest.raises(OSError):
            await coordinator.refresh(enabled=True)
    sync_repair(hass, coordinator)
    fetch.assert_not_awaited()
    assert await coordinator.refresh(enabled=True) == 'skipped'
    issue = ir.async_get(hass).async_get_issue('terralyra_ignis', 'test-nifc_nifc_research')
    assert issue.translation_key == 'nifc_storage_save'
    assert 'private' not in str(coordinator.diagnostics())


async def test_missing_store_repair_and_explicit_valid_recovery(hass, hass_storage, research):
    from homeassistant.helpers import issue_registry as ir
    coordinator_type, result_type = research
    store = Store(hass, 1, KEY)
    fetch = AsyncMock(return_value=result_type((), 1, 1, 'terminal_reported'))
    coordinator = coordinator_type(store, fetcher=fetch)
    with pytest.raises(ValueError):
        await coordinator.setup()
    sync_repair(hass, coordinator)
    sync_repair(hass, coordinator, 'other-entry')
    registry = ir.async_get(hass)
    assert registry.async_get_issue('terralyra_ignis', 'test-nifc_nifc_research').translation_key == 'nifc_storage_load'
    # Explicit synthetic setup, not an automatic reset or a production repair action.
    await store.async_save({'version': 1, 'wait_seconds': 0, 'failures': 0})
    await coordinator.setup()
    assert await coordinator.refresh(enabled=True) == 'retrieved'
    sync_repair(hass, coordinator)
    assert registry.async_get_issue('terralyra_ignis', 'test-nifc_nifc_research') is None
    assert registry.async_get_issue('terralyra_ignis', 'other-entry_nifc_research') is not None
    fetch.assert_awaited_once()


async def test_cancelled_fetch_retains_pause_and_repair_after_reload(hass, hass_storage, research):
    import asyncio
    from homeassistant.helpers import issue_registry as ir
    coordinator_type, _ = research
    store = Store(hass, 1, KEY)
    await store.async_save({'version': 1, 'wait_seconds': 0, 'failures': 0})
    entered = asyncio.Event()
    async def fetch():
        entered.set()
        await asyncio.Future()
    coordinator = coordinator_type(store, fetcher=fetch)
    await coordinator.setup()
    task = asyncio.create_task(coordinator.refresh(enabled=True))
    await entered.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    restored_fetch = AsyncMock()
    restored = coordinator_type(Store(hass, 1, KEY), fetcher=restored_fetch)
    await restored.setup()
    assert await restored.refresh(enabled=True) == 'skipped'
    sync_repair(hass, restored)
    issue = ir.async_get(hass).async_get_issue('terralyra_ignis', 'test-nifc_nifc_research')
    assert issue.translation_key == 'nifc_review_required'
    restored_fetch.assert_not_awaited()
