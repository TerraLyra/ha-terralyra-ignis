"""Real HA Store tests: no upstream network or production storage."""
import asyncio
from unittest.mock import AsyncMock
from datetime import datetime, UTC
import pytest
from homeassistant.helpers.storage import Store
from custom_components.terralyra_ignis.official_sources.tasalert.owner import TasAlertOwner, STORE_KEY
from custom_components.terralyra_ignis.official_sources.tasalert.engine import Engine
from custom_components.terralyra_ignis.official_sources.tasalert.engine_storage import encode
from custom_components.terralyra_ignis.official_sources.tasalert.policy import State


async def test_real_store_restart_preserves_cooldown(hass,hass_storage):
    store=Store(hass,1,STORE_KEY)
    owner=TasAlertOwner(store,None)
    await owner.async_load(confirmed_new=True)
    candidate=Engine(response=State(failures=2,next_attempt=datetime(2030,1,1,tzinfo=UTC),status='retrieval_failed'))
    owner.fetcher=AsyncMock(return_value=candidate)
    await owner.async_refresh()
    restored=TasAlertOwner(Store(hass,1,STORE_KEY),None)
    await restored.async_load()
    assert restored.state==candidate
    await owner.async_close();await restored.async_close()


async def test_corrupt_real_store_is_not_reset(hass,hass_storage):
    store=Store(hass,1,STORE_KEY)
    await store.async_save({'version':999})
    owner=TasAlertOwner(store,None)
    with pytest.raises(ValueError):await owner.async_load(confirmed_new=True)
    assert owner.blocked
    assert await store.async_load()=={'version':999}


async def test_close_cancels_fetch_without_save(hass,hass_storage):
    owner=TasAlertOwner(Store(hass,1,STORE_KEY),None)
    await owner.async_load(confirmed_new=True)
    started=asyncio.Event()
    async def fetch(*args,**kwargs):
        started.set();await asyncio.Event().wait()
    owner.fetcher=fetch
    task=asyncio.create_task(owner.async_refresh())
    await started.wait();await owner.async_close()
    assert task.cancelled()
    assert owner.state==Engine()
    with pytest.raises(OSError):await owner.async_refresh()


async def test_storage_timeout_latches_block():
    release=asyncio.Event()
    async def stalled():await release.wait();return None
    store=AsyncMock();store.async_load=stalled
    owner=TasAlertOwner(store,None,storage_timeout=.01)
    with pytest.raises(OSError):await owner.async_load(confirmed_new=True)
    assert owner.blocked
    release.set();await owner._pending
    store.async_save.assert_not_awaited()


async def test_recovery_waits_for_pending_write_and_preserves_longer_pause(hass,hass_storage):
    from datetime import timedelta
    owner=TasAlertOwner(Store(hass,1,STORE_KEY),None)
    await owner.async_load(confirmed_new=True)
    future=datetime.now(UTC)+timedelta(days=2)
    candidate=Engine(response=State(failures=2,next_attempt=future,status='retrieval_failed'))
    owner.fetcher=AsyncMock(return_value=candidate)
    await owner.async_refresh()
    release=asyncio.Event()
    owner._pending=asyncio.create_task(release.wait())
    owner.blocked=True
    with pytest.raises(OSError):await owner.async_recover()
    release.set();await owner._pending
    await owner.async_recover()
    assert owner.state.response.next_attempt==future
    assert not owner.blocked
    assert owner.state.response.failures==2
    await owner.async_close()
