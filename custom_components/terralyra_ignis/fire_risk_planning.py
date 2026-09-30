"""Pure opt-in forecast planning; no configuration writes or network requests."""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, replace

from .const import MAX_MONITORED_LOCATIONS
from .core.locations import MonitoredLocation, validate_monitored_locations
from .fire_risk_context import FireRiskRequestContext
from .fire_risk_coverage import plan_fire_risk_sources
from .products.fire_risk import FireRiskError


@dataclass(frozen=True, slots=True)
class LocationForecastSettings:
    """Explicit forecast opt-in with a radius independent of fire monitoring."""

    location_id: str
    enabled: bool
    radius_km: float

    def __post_init__(self) -> None:
        if (
            not isinstance(self.location_id, str)
            or not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", self.location_id)
            or type(self.enabled) is not bool
            or isinstance(self.radius_km, bool)
            or not isinstance(self.radius_km, (int, float))
            or not math.isfinite(self.radius_km)
            or not 1 <= self.radius_km <= 500
        ):
            raise FireRiskError("Invalid location forecast settings")

    def as_dict(self) -> dict[str, str | bool | float]:
        return dict(location_id=self.location_id, enabled=self.enabled,
                    radius_km=self.radius_km)

    @classmethod
    def from_dict(cls, value: object) -> LocationForecastSettings:
        """Reject incomplete/unknown fields instead of enabling implicit defaults."""
        if not isinstance(value, dict) or set(value) != {"location_id", "enabled", "radius_km"}:
            raise FireRiskError("Invalid location forecast settings")
        return cls(**value)


@dataclass(frozen=True, slots=True)
class LocationForecastDecision:
    """A geographic plan, never evidence of a received or active forecast."""

    location_id: str
    reason: str
    contexts: tuple[FireRiskRequestContext, ...] = ()
    coverage: tuple[str, ...] = ()


def plan_location_forecasts(
    locations: tuple[MonitoredLocation, ...],
    settings: tuple[LocationForecastSettings, ...],
) -> tuple[LocationForecastDecision, ...]:
    """Plan explicit settings only, bounded to the supported location count.

    Missing locations retain an inert decision, so callers need not delete
    settings/history to handle removal. The legacy HA Home request is separate.
    """
    if len(locations) > MAX_MONITORED_LOCATIONS or len(settings) > MAX_MONITORED_LOCATIONS:
        raise FireRiskError("Too many forecast locations")
    validate_monitored_locations(locations)
    if len({item.location_id for item in settings}) != len(settings):
        raise FireRiskError("Duplicate forecast location settings")
    by_id = {item.id: item for item in locations}
    decisions = []
    for item in settings:
        location = by_id.get(item.location_id)
        if not item.enabled:
            reason = "forecast_disabled"
        elif location is None:
            reason = "location_missing"
        elif not location.enabled:
            reason = "location_disabled"
        else:
            # Coverage must use the forecast radius, not the satellite radius.
            plan = plan_fire_risk_sources(replace(location, radius_km=item.radius_km))
            decisions.append(LocationForecastDecision(
                item.location_id,
                "eligible" if plan.covered else "no_compatible_fire_risk_source",
                tuple(FireRiskRequestContext(
                    location.id, source.provider, source.product,
                    location.latitude, location.longitude, item.radius_km,
                ) for source in plan.assignments),
                tuple(source.coverage for source in plan.assignments),
            ))
            continue
        decisions.append(LocationForecastDecision(item.location_id, reason))
    return tuple(decisions)


CONF_LOCATION_FORECASTS = "location_forecasts"


def decode_forecast_settings(value: object) -> tuple[LocationForecastSettings, ...]:
    """Read bounded explicit options; never infer defaults from other radii."""
    if not isinstance(value, list) or len(value) > MAX_MONITORED_LOCATIONS:
        raise FireRiskError("Invalid location forecast settings list")
    settings = tuple(LocationForecastSettings.from_dict(item) for item in value)
    if len({item.location_id for item in settings}) != len(settings):
        raise FireRiskError("Duplicate location forecast settings")
    return settings
