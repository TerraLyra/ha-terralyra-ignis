"""Only current forecasts with matching immutable location identity are shown."""
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock

import pytest

from custom_components.terralyra_ignis.fire_risk_context import FireRiskRequestContext
from custom_components.terralyra_ignis.location_fire_risk_coordinator import LocationFireRiskForecast
from custom_components.terralyra_ignis.location_fire_risk_sensor import LocationFireRiskSensor
from custom_components.terralyra_ignis.products.fire_risk import FireRiskDay, FireRiskForecast


def make():
    context = FireRiskRequestContext('one', 'eumetsat_lsa_saf_frmv3', 'FRMv3', 47., 19., 50.)
    forecast = FireRiskForecast(47.05, 19.05, datetime.now(UTC),
        (FireRiskDay(datetime.now(UTC).date(), 3),), 4, 47.1, 19.1, 50.)
    coordinator = Mock(context=context, data=LocationFireRiskForecast(context, forecast), last_update_success=True)
    return LocationFireRiskSensor(Mock(entry_id='entry'), coordinator, 'Cabin'), coordinator


def test_current_location_binding_and_sample_are_distinct():
    sensor, coordinator = make()
    assert sensor.available
    assert sensor.native_value == 'high'
    attrs = sensor.extra_state_attributes
    assert attrs['location_id'] == 'one'
    assert attrs['latitude'] == 47.
    assert attrs['sample_latitude'] == 47.05
    assert attrs['forecast_radius_km'] == 50.
    assert attrs['time_semantics'] == 'retrieval_time_not_issuance'
    assert sensor.unique_id == 'entry_location_fire_risk_one'


@pytest.mark.parametrize('problem', ['missing', 'failed', 'identity', 'yesterday', 'empty'])
def test_unavailable_or_wrong_result_cannot_be_displayed(problem):
    sensor, coordinator = make()
    result = coordinator.data
    if problem == 'missing':
        coordinator.data = None
    elif problem == 'failed':
        coordinator.last_update_success = False
    elif problem == 'identity':
        coordinator.data = replace(result, context=replace(result.context, location_id='other'))
    else:
        days = () if problem == 'empty' else (FireRiskDay(datetime.now(UTC).date() - timedelta(days=1), 1),)
        coordinator.data = replace(result, forecast=replace(result.forecast, days=days))
    assert not sensor.available
    assert sensor.native_value is None
    assert sensor.extra_state_attributes['forecast'] == []


async def test_midnight_refresh_and_timer_cleanup(hass, monkeypatch):
    sensor, _ = make()
    sensor.hass = hass
    timer = Mock(return_value=Mock())
    monkeypatch.setattr('custom_components.terralyra_ignis.location_fire_risk_sensor.async_track_point_in_utc_time', timer)
    sensor.async_write_ha_state = Mock()
    sensor._schedule_midnight()
    assert timer.call_args.args[2].hour == 0
    assert timer.call_args.args[2].date() == datetime.now(UTC).date() + timedelta(days=1)
    sensor._midnight(None)
    sensor.async_write_ha_state.assert_called_once()
    await sensor.async_will_remove_from_hass()
    timer.return_value.assert_called_once()
