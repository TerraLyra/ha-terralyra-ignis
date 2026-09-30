"""Request contexts must never mix coordinates or inherit active-fire geometry."""
from dataclasses import FrozenInstanceError
from unittest.mock import Mock, AsyncMock

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.terralyra_ignis.const import DEFAULT_RADIUS_KM
from custom_components.terralyra_ignis.fire_risk_context import FireRiskRequestContext
from custom_components.terralyra_ignis.fire_risk_coordinator import FireRiskCoordinator
from custom_components.terralyra_ignis.products.fire_risk import FireRiskError


def context(**changes):
    values = dict(location_id="ha-home", provider="eumetsat_lsa_saf_frmv3",
                  product="FRMv3", latitude=47.5, longitude=19.0, radius_km=100)
    return FireRiskRequestContext(**(values | changes))


@pytest.mark.parametrize("changes", [
    {"latitude": float("nan")}, {"longitude": 181}, {"radius_km": 0},
    {"radius_km": 501}, {"radius_km": True}, {"latitude": "47"},
    {"location_id": ""}, {"location_id": "other/place"}, {"product": None},
])
def test_invalid_request_context(changes):
    with pytest.raises(FireRiskError):
        context(**changes)


def test_context_is_immutable_and_independent():
    home = context()
    other = context(location_id="other", latitude=48, radius_km=25)
    assert (home.latitude, home.radius_km) == (47.5, 100)
    assert (other.latitude, other.radius_km) == (48, 25)
    with pytest.raises(FrozenInstanceError):
        home.latitude = 48


@pytest.mark.parametrize(("options", "expected"), [
    ({"fire_risk_radius_km": 25, "radius_km": 200}, 25),
    ({"radius_km": 200}, 200),
    ({}, DEFAULT_RADIUS_KM),
])
def test_legacy_home_context_parity(hass, options, expected):
    hass.config.latitude, hass.config.longitude = 47.5, 19.0
    coordinator = FireRiskCoordinator(hass, Mock(entry_id="test", options=options), Mock())
    result = coordinator._home_request_context()
    assert (result.location_id, result.latitude, result.longitude, result.radius_km) == (
        "ha-home", 47.5, 19.0, expected)
    hass.config.latitude = 48.0
    assert coordinator._home_request_context().latitude == 48.0
    assert result.latitude == 47.5


async def test_invalid_geometry_does_not_fetch(hass, monkeypatch):
    client = Mock(async_forecast=AsyncMock())
    coordinator = FireRiskCoordinator(hass, Mock(entry_id="test", options={"fire_risk_radius_km": 501}), client)
    monkeypatch.setattr("custom_components.terralyra_ignis.fire_risk_coordinator.async_set_fire_risk_outage_issue", Mock())
    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()
    client.async_forecast.assert_not_called()


async def test_refresh_uses_one_home_context(hass, monkeypatch):
    from datetime import date
    hass.config.latitude, hass.config.longitude = 47.5, 19.0
    forecast = Mock(days=[Mock(valid_date=date(2026, 9, 30))])
    client = Mock(async_forecast=AsyncMock(return_value=forecast),
                  async_map=AsyncMock(side_effect=FireRiskError("map unavailable")))
    coordinator = FireRiskCoordinator(hass, Mock(entry_id="test", options={
        "fire_risk_radius_km": 25, "radius_km": 200,
    }), client)
    monkeypatch.setattr("custom_components.terralyra_ignis.fire_risk_coordinator.async_set_fire_risk_outage_issue", Mock())
    interval = coordinator.update_interval
    assert await coordinator._async_update_data() is forecast
    client.async_forecast.assert_awaited_once_with(47.5, 19.0, 25.0)
    client.async_map.assert_awaited_once()
    assert coordinator.update_interval == interval
