"""Cross-location forecast decisions must not turn coverage into live data."""
from dataclasses import replace

import pytest

from custom_components.terralyra_ignis.core.locations import MonitoredLocation
from custom_components.terralyra_ignis.fire_risk_planning import (
    LocationForecastSettings as Settings, plan_location_forecasts,
)
from custom_components.terralyra_ignis.products.fire_risk import FireRiskError


def location(id="one", **changes):
    values = dict(id=id, name="Same name", latitude=47.5, longitude=19.0,
                  radius_km=500, enabled=True, source="manual")
    return MonitoredLocation(**(values | changes))


@pytest.mark.parametrize("value", [
    {}, {"location_id": "one", "enabled": True},
    {"location_id": "one", "enabled": "false", "radius_km": 10},
    {"location_id": "one", "enabled": True, "radius_km": True},
    {"location_id": "one", "enabled": True, "radius_km": float("nan")},
    {"location_id": "one", "enabled": True, "radius_km": 501},
    {"location_id": "one", "enabled": True, "radius_km": 10, "extra": 1},
])
def test_settings_require_explicit_valid_values(value):
    with pytest.raises(FireRiskError):
        Settings.from_dict(value)


def test_roundtrip_and_no_implicit_activation():
    setting = Settings("one", True, 25)
    assert Settings.from_dict(setting.as_dict()) == setting
    assert plan_location_forecasts((location(),), ()) == ()


def test_separate_identity_and_forecast_radius():
    locations = (location(), location("two", latitude=48.5))
    settings = (Settings("one", True, 25), Settings("two", True, 50))
    plans = plan_location_forecasts(locations, settings)
    assert [p.reason for p in plans] == ["eligible", "eligible"]
    assert [(p.contexts[0].location_id, p.contexts[0].latitude, p.contexts[0].radius_km)
            for p in plans] == [("one", 47.5, 25), ("two", 48.5, 50)]
    renamed = tuple(replace(l, name="Renamed") for l in reversed(locations))
    assert plan_location_forecasts(renamed, settings) == plans


def test_inert_locations_never_get_contexts():
    locations = (location(), location("off", enabled=False),
                 location("tokyo", latitude=35.6, longitude=139.6))
    plans = plan_location_forecasts(locations, (
        Settings("one", False, 25), Settings("off", True, 25),
        Settings("missing", True, 25), Settings("tokyo", True, 25),
    ))
    assert [p.reason for p in plans] == ["forecast_disabled", "location_disabled",
                                        "location_missing", "no_compatible_fire_risk_source"]
    assert all(not p.contexts for p in plans)


def test_coverage_uses_forecast_radius():
    plans = plan_location_forecasts((location(latitude=35, longitude=-9.5),),
                                    (Settings("one", True, 1),))
    assert plans[0].coverage == ("full_radius",)
    larger = plan_location_forecasts((location(latitude=35, longitude=-9.5),),
                                     (Settings("one", True, 100),))
    assert larger[0].coverage == ("radius_clipped_to_product_bounds",)


def test_duplicate_and_oversized_plans_rejected():
    with pytest.raises(FireRiskError):
        plan_location_forecasts((location(),), (Settings("one", True, 25),) * 2)
    with pytest.raises(FireRiskError):
        plan_location_forecasts(tuple(location(str(i)) for i in range(11)), ())
    with pytest.raises(FireRiskError):
        plan_location_forecasts((), tuple(Settings(str(i), True, 25) for i in range(11)))
    with pytest.raises(ValueError):
        plan_location_forecasts((location(), location()), ())


def test_ten_locations_and_settings_are_bounded():
    places = tuple(location(str(i)) for i in range(10))
    settings = tuple(Settings(str(i), True, 25) for i in range(10))
    assert sum(len(p.contexts) for p in plan_location_forecasts(places, settings)) == 10


async def test_frmv3_point_request_budget():
    from unittest.mock import AsyncMock
    from custom_components.terralyra_ignis.products.fire_risk import FireRiskClient
    client = FireRiskClient(object())
    # Worst valid path: eight nodata samples, ninth succeeds, then nine days.
    client._async_point = AsyncMock(side_effect=[None] * 8 + [3] * 10)
    result = await client.async_forecast(47.5, 19.0, 25)
    assert len(result.days) == 10
    assert client._async_point.await_count == 18
