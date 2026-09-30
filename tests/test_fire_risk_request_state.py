"""Durable cooldowns must survive restart and storage failures without traffic."""
import asyncio
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock

import pytest

from custom_components.terralyra_ignis.fire_risk_request_state import (
    ForecastStateError, PersistentForecastRequestGate,
)
from custom_components.terralyra_ignis.fire_risk_requests import ForecastRequestDeferred
from custom_components.terralyra_ignis.products.fire_risk import FireRiskClient, FireRiskRateLimitError

NOW = datetime(2026, 9, 30, tzinfo=UTC)


def store(payload=None):
    return Mock(async_load=AsyncMock(return_value=payload), async_save=AsyncMock())


def gate(storage, now=NOW):
    return PersistentForecastRequestGate(storage, clock=lambda: 10., utcnow=lambda: now)


async def test_restart_restores_pause_before_any_http():
    storage = store()
    first = gate(storage)
    failure = AsyncMock(side_effect=FireRiskRateLimitError('limited', 429))
    with pytest.raises(FireRiskRateLimitError):
        await first.run(failure)
    saved = storage.async_save.call_args.args[0]
    assert saved['provider'] == 'eumetsat_lsa_saf_frmv3'
    restarted = gate(store(saved), NOW + timedelta(minutes=5))
    network = AsyncMock()
    with pytest.raises(ForecastRequestDeferred) as exc:
        await restarted.run(network)
    assert exc.value.retry_after == timedelta(minutes=10)
    network.assert_not_awaited()


async def test_failed_load_is_retried_without_network():
    storage = store()
    storage.async_load.side_effect = [OSError(), None]
    shared = gate(storage)
    network = AsyncMock(return_value=b'ok')
    with pytest.raises(ForecastStateError):
        await shared.run(network)
    network.assert_not_awaited()
    assert await shared.run(network) == b'ok'
    assert storage.async_load.await_count == 2


async def test_failed_write_remains_dirty_and_blocks_peers():
    storage = store()
    storage.async_save.side_effect = [OSError(), OSError(), None]
    shared = gate(storage)
    with pytest.raises(ForecastStateError):
        await shared.run(AsyncMock(side_effect=FireRiskRateLimitError('limited', 429)))
    peer = AsyncMock()
    with pytest.raises(ForecastStateError):
        await shared.run(peer)
    with pytest.raises(ForecastRequestDeferred):
        await shared.run(peer)
    peer.assert_not_awaited()
    assert storage.async_load.await_count == 1
    assert storage.async_save.await_count == 3


@pytest.mark.parametrize('payload', [False, {}, {'schema': True},
    {'schema': 1, 'provider': 'wrong', 'cooldown': None},
    *[{'schema': 1, 'provider': 'eumetsat_lsa_saf_frmv3',
       'cooldown': {'schema': 1, 'until': until}} for until in
      ('invalid', '2026-09-30T00:10:00', '2026-10-01T00:10:00+00:00')]])
async def test_invalid_state_does_not_allow_network(payload):
    network = AsyncMock()
    with pytest.raises(ForecastStateError):
        await gate(store(payload)).run(network)
    network.assert_not_awaited()


async def test_expired_pause_allows_request_without_rewriting_history():
    storage = store({'schema': 1, 'provider': 'eumetsat_lsa_saf_frmv3',
        'cooldown': {'schema': 1, 'until': (NOW - timedelta(seconds=1)).isoformat()}})
    assert await gate(storage).run(AsyncMock(return_value=42)) == 42
    storage.async_save.assert_not_awaited()


async def test_cancelled_save_remains_dirty():
    storage = store()
    storage.async_save.side_effect = [asyncio.CancelledError(), None]
    shared = gate(storage)
    with pytest.raises(asyncio.CancelledError):
        await shared.run(AsyncMock(side_effect=FireRiskRateLimitError('limited', 429)))
    peer = AsyncMock()
    with pytest.raises(ForecastRequestDeferred):
        await shared.run(peer)
    peer.assert_not_awaited()
    assert storage.async_save.await_count == 2


async def test_two_clients_share_one_restored_gate():
    storage = store()
    shared = gate(storage)
    first = FireRiskClient(Mock(), request_gate=shared)
    second = FireRiskClient(Mock(), request_gate=shared)
    first._async_get_direct = AsyncMock(side_effect=FireRiskRateLimitError('limited', 429))
    second._async_get_direct = AsyncMock()
    with pytest.raises(FireRiskRateLimitError):
        await first._async_get({'REQUEST': 'GetFeatureInfo'}, 100)
    with pytest.raises(ForecastRequestDeferred):
        await second._async_get({'REQUEST': 'GetMap'}, 200)
    second._async_get_direct.assert_not_awaited()
    storage.async_load.assert_awaited_once()


async def test_legacy_client_does_not_use_gate():
    client = FireRiskClient(Mock())
    client._async_get_direct = AsyncMock(return_value=b'ok')
    assert await client._async_get({'REQUEST': 'GetCapabilities'}, 50) == b'ok'
    client._async_get_direct.assert_awaited_once_with({'REQUEST': 'GetCapabilities'}, 50)


async def test_peer_waits_until_cooldown_is_durable():
    storage = store()
    saving, finish = asyncio.Event(), asyncio.Event()

    async def save(data):
        saving.set()
        await finish.wait()

    storage.async_save.side_effect = save
    shared = gate(storage)
    first = asyncio.create_task(shared.run(
        AsyncMock(side_effect=FireRiskRateLimitError('limited', 429))))
    await saving.wait()
    operation = AsyncMock()
    peer = asyncio.create_task(shared.run(operation))
    await asyncio.sleep(0)
    assert not peer.done()
    operation.assert_not_awaited()
    finish.set()
    with pytest.raises(FireRiskRateLimitError):
        await first
    with pytest.raises(ForecastRequestDeferred):
        await peer
    operation.assert_not_awaited()
