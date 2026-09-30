"""Opt-in lifecycle scheduling: no I/O at construction, no work after close."""
import asyncio
from dataclasses import replace
from unittest.mock import AsyncMock, Mock

import pytest

from custom_components.terralyra_ignis.core.locations import MonitoredLocation
from custom_components.terralyra_ignis.fire_risk_planning import LocationForecastSettings
from custom_components.terralyra_ignis.location_fire_risk_runtime import LocationForecastRuntime

LOCATION = MonitoredLocation('one', 'Same name', 47.5, 19., 500., True, 'manual')


@pytest.fixture
def lifecycle(monkeypatch):
    created, scheduled = [], []

    def factory(hass, entry, session, context, gate):
        value = Mock(context=context, async_refresh=AsyncMock(), async_shutdown=AsyncMock())
        value.async_add_listener.return_value = Mock()
        value.gate = gate
        created.append(value)
        return value

    def later(hass, delay, action):
        cancel = Mock()
        scheduled.append((delay, action, cancel))
        return cancel

    monkeypatch.setattr('custom_components.terralyra_ignis.location_fire_risk_runtime.LocationFireRiskCoordinator', factory)
    monkeypatch.setattr('custom_components.terralyra_ignis.location_fire_risk_runtime.async_call_later', later)
    entry = Mock(entry_id='entry', pref_disable_polling=False)
    entry.async_create_background_task.side_effect = lambda hass, coro, name: asyncio.create_task(coro)
    return created, scheduled, entry


def owner(lifecycle, locations=(LOCATION,), settings=None):
    _, _, entry = lifecycle
    if settings is None:
        settings = tuple(LocationForecastSettings(item.id, True, 50) for item in locations)
    return LocationForecastRuntime(Mock(), entry, Mock(), locations, settings, Mock())


async def test_constructs_only_explicitly_enabled_eligible_locations(lifecycle):
    created, scheduled, _ = lifecycle
    locations = (LOCATION, replace(LOCATION, id='disabled', enabled=False),
                 replace(LOCATION, id='outside', latitude=-30), replace(LOCATION, id='opted-out'))
    settings = tuple(LocationForecastSettings(item.id, item.id != 'opted-out', 50) for item in locations)
    runtime = owner(lifecycle, locations, settings)
    assert list(runtime.coordinators) == ['one']
    assert not scheduled
    created[0].async_refresh.assert_not_awaited()
    await runtime.close()


async def test_missing_settings_do_not_activate_locations(lifecycle):
    runtime = owner(lifecycle, settings=())
    runtime.start()
    assert not lifecycle[0] and not lifecycle[1]
    await runtime.close()


async def test_startup_stagger_bounded_and_order_independent(lifecycle):
    created, scheduled, _ = lifecycle
    locations = tuple(replace(LOCATION, id=f'place-{i}') for i in range(10))
    first = owner(lifecycle, locations)
    first.start()
    delays = [row[0] for row in scheduled]
    assert len(delays) == 10
    assert all(30 <= delay <= 314 for delay in delays)
    assert all(b - a >= 16 for a, b in zip(delays, delays[1:]))
    assert len({id(coordinator.gate) for coordinator in created}) == 1
    first.start()
    assert len(scheduled) == 10
    await first.close()
    scheduled.clear()
    second = owner(lifecycle, tuple(reversed(locations)))
    second.start()
    assert [row[0] for row in scheduled] == delays
    await second.close()


async def test_close_cancels_timers_and_stale_callbacks(lifecycle):
    created, scheduled, _ = lifecycle
    runtime = owner(lifecycle)
    runtime.start()
    _, action, cancel = scheduled[0]
    await runtime.close()
    cancel.assert_called_once()
    created[0].async_add_listener.return_value.assert_called_once()
    action(None)
    runtime.start()
    created[0].async_refresh.assert_not_awaited()
    assert len(scheduled) == 1


async def test_close_cancels_started_initial_refresh(lifecycle):
    created, scheduled, _ = lifecycle
    runtime = owner(lifecycle)
    started = asyncio.Event()

    async def refresh():
        started.set()
        await asyncio.Event().wait()

    created[0].async_refresh.side_effect = refresh
    runtime.start()
    scheduled[0][1](None)
    await started.wait()
    task = next(iter(runtime._tasks))
    await runtime.close()
    assert task.cancelled()
    assert not runtime._tasks
    created[0].async_shutdown.assert_awaited_once()


async def test_respects_ha_disabled_polling(lifecycle):
    created, scheduled, entry = lifecycle
    entry.pref_disable_polling = True
    runtime = owner(lifecycle)
    runtime.start()
    assert not scheduled
    created[0].async_add_listener.assert_not_called()
    await runtime.close()
