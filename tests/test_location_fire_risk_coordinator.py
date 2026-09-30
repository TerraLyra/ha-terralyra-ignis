"""Location forecasts preserve identity and isolate geometry, cache and failures."""
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.terralyra_ignis.fire_risk_context import FireRiskRequestContext
from custom_components.terralyra_ignis.fire_risk_request_state import PersistentForecastRequestGate
from custom_components.terralyra_ignis.fire_risk_requests import ForecastRequestDeferred
from custom_components.terralyra_ignis.location_fire_risk_coordinator import LocationFireRiskCoordinator
from custom_components.terralyra_ignis.products.fire_risk import FireRiskDay, FireRiskError, FireRiskForecast

CONTEXT = FireRiskRequestContext('location-a', 'eumetsat_lsa_saf_frmv3', 'FRMv3', 47.5, 19., 50.)


def make(hass, context=CONTEXT, entry_id='entry-a'):
    gate = PersistentForecastRequestGate(Mock(async_load=AsyncMock(return_value=None)))
    return LocationFireRiskCoordinator(hass, Mock(entry_id=entry_id), Mock(), context, gate)


def forecast(level=2):
    return FireRiskForecast(47.55, 19.05, datetime.now(UTC),
        (FireRiskDay(datetime.now(UTC).date(), level),), level, 47.55, 19.05, 50.)


async def test_uses_explicit_location_not_home(hass):
    hass.config.latitude, hass.config.longitude = 1., 2.
    coordinator = make(hass)
    value = forecast()
    coordinator.client.async_forecast = AsyncMock(return_value=value)
    coordinator.client.async_map = AsyncMock(side_effect=FireRiskError('map missing'))
    result = await coordinator._async_update_data()
    coordinator.client.async_forecast.assert_awaited_once_with(47.5, 19., 50.)
    assert result.context == CONTEXT
    assert result.forecast is value
    assert result.forecast.latitude != result.context.latitude


@pytest.mark.parametrize('context', [replace(CONTEXT, provider='other'),
    replace(CONTEXT, product='other'), replace(CONTEXT, latitude=-30.)])
def test_rejects_unsupported_context_without_requests(hass, context):
    with pytest.raises(FireRiskError):
        make(hass, context)


def test_cache_and_client_are_isolated(hass):
    original = make(hass)
    for other in (make(hass, replace(CONTEXT, location_id='location-b')),
                  make(hass, replace(CONTEXT, longitude=19.01)),
                  make(hass, replace(CONTEXT, radius_km=60.)),
                  make(hass, entry_id='entry-b')):
        assert other._map_store.key != original._map_store.key
        assert other.client is not original.client
    assert make(hass)._map_store.key == original._map_store.key
    assert not original._map_store.key.endswith('.fire_risk_map')


async def test_local_deferral_does_not_increment_failure_count(hass):
    coordinator = make(hass)
    coordinator._consecutive_failures = 2
    coordinator.client.async_forecast = AsyncMock(side_effect=ForecastRequestDeferred(timedelta(minutes=40)))
    coordinator.client.async_map = AsyncMock()
    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()
    assert coordinator._consecutive_failures == 2
    assert coordinator.update_interval == timedelta(minutes=40)
    coordinator.client.async_map.assert_not_awaited()


async def test_failure_of_one_location_does_not_replace_peer_data(hass):
    first = make(hass)
    peer = make(hass, replace(CONTEXT, location_id='location-b'))
    previous = object()
    peer.data = previous
    first.client.async_forecast = AsyncMock(side_effect=FireRiskError('unavailable'))
    with pytest.raises(UpdateFailed):
        await first._async_update_data()
    assert first._consecutive_failures == 1
    assert peer._consecutive_failures == 0
    assert peer.data is previous


async def test_map_deferral_keeps_point_data_and_reschedules(hass):
    coordinator = make(hass)
    value = forecast()
    coordinator.client.async_forecast = AsyncMock(return_value=value)
    coordinator.client.async_map = AsyncMock(side_effect=ForecastRequestDeferred(timedelta(minutes=30)))
    result = await coordinator._async_update_data()
    assert result.forecast is value
    assert coordinator.update_interval == timedelta(minutes=30)
    assert coordinator._consecutive_failures == 0


async def test_restores_only_matching_scoped_cache(hass, monkeypatch):
    coordinator = make(hass)
    payload = {'test': 'payload'}
    coordinator._map_store = Mock(async_load=AsyncMock(return_value=payload))
    importer = Mock(return_value=False)
    monkeypatch.setattr('custom_components.terralyra_ignis.location_fire_risk_coordinator.import_scoped_map_cache', importer)
    await coordinator._async_setup()
    importer.assert_called_once_with(coordinator.client, CONTEXT, payload)
    coordinator._map_store.async_save.assert_not_called()


@pytest.mark.parametrize('save_error', [None, OSError('disk unavailable')])
async def test_successful_map_keeps_scope_even_when_cache_write_fails(hass, monkeypatch, save_error):
    coordinator = make(hass)
    coordinator.client.async_forecast = AsyncMock(return_value=forecast())
    coordinator.client.async_map = AsyncMock(return_value=b'image')
    coordinator.client.export_map_cache = Mock(return_value={'provider': 'cache'})
    coordinator._map_store = Mock(async_save=AsyncMock(side_effect=save_error))
    monkeypatch.setattr('custom_components.terralyra_ignis.location_fire_risk_coordinator.analyze_risk_map',
                        Mock(return_value=(4, 47.6, 19.1)))
    result = await coordinator._async_update_data()
    assert result.context == CONTEXT
    assert result.forecast.area_level == 4
    assert result.forecast.days[0].level == 2
    coordinator._map_store.async_save.assert_awaited_once_with(
        CONTEXT.wrap_map_cache({'provider': 'cache'}))
    assert coordinator.update_interval == coordinator._normal_interval


def test_requires_persistent_shared_gate(hass):
    with pytest.raises(FireRiskError):
        LocationFireRiskCoordinator(hass, Mock(entry_id='entry-a'), Mock(), CONTEXT, None)


@pytest.mark.parametrize('days', [(), (FireRiskDay(datetime.now(UTC).date() - timedelta(days=1), 1),)])
async def test_missing_or_old_product_day_is_not_current(hass, days):
    coordinator = make(hass)
    coordinator.client.async_forecast = AsyncMock(return_value=replace(forecast(), days=days))
    coordinator.client.async_map = AsyncMock()
    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()
    coordinator.client.async_map.assert_not_awaited()
    assert coordinator._consecutive_failures == 1


async def test_midnight_during_map_retrieval_does_not_publish_old_day(hass, monkeypatch):
    coordinator = make(hass)
    value = forecast()
    coordinator.client.async_forecast = AsyncMock(return_value=value)
    coordinator.client.async_map = AsyncMock(side_effect=FireRiskError('map unavailable'))
    clock = Mock()
    clock.now.side_effect = [value.generated_at, value.generated_at + timedelta(days=1)]
    monkeypatch.setattr('custom_components.terralyra_ignis.location_fire_risk_coordinator.datetime', clock)
    with pytest.raises(UpdateFailed, match='expired'):
        await coordinator._async_update_data()
    assert coordinator.update_interval == timedelta(minutes=15)
