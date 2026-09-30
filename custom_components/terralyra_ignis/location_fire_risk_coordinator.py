"""Explicit-context FRMv3 coordinator; not activated by integration setup yet."""
from __future__ import annotations

import logging
from dataclasses import dataclass, replace
from datetime import timedelta

from aiohttp import ClientSession
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN
from .fire_risk_cache import import_scoped_map_cache
from .fire_risk_context import FireRiskRequestContext
from .fire_risk_coordinator import _retry_interval, _staggered_interval
from .fire_risk_coverage import FIRE_RISK_PROVIDER_LSA_SAF
from .fire_risk_request_state import PersistentForecastRequestGate
from .fire_risk_requests import ForecastRequestDeferred
from .products.fire_risk import (
    EUROPE_BOUNDS, PRODUCT_ID, FireRiskClient, FireRiskError, FireRiskForecast,
    analyze_risk_map, map_bounds, safe_fire_risk_reason,
)

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class LocationFireRiskForecast:
    """Keep the requested location distinct from the provider's sampled pixel."""

    context: FireRiskRequestContext
    forecast: FireRiskForecast


class LocationFireRiskCoordinator(DataUpdateCoordinator[LocationFireRiskForecast]):
    """Own one immutable geometry and one client cache, sharing provider pacing.

    The runtime owner must only construct this for an explicitly enabled eligible
    plan and must replace/unload it when geometry or enabled state changes.
    Construction alone starts no request. Existing Home coordinator is unchanged.
    """

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, session: ClientSession,
        context: FireRiskRequestContext, request_gate: PersistentForecastRequestGate,
    ) -> None:
        west, south, east, north = EUROPE_BOUNDS
        if (context.provider != FIRE_RISK_PROVIDER_LSA_SAF or context.product != PRODUCT_ID
                or not west <= context.longitude <= east
                or not south <= context.latitude <= north
                or not isinstance(request_gate, PersistentForecastRequestGate)):
            raise FireRiskError("Unsupported location forecast context or request gate")
        self._context = context
        self.client = FireRiskClient(session, request_gate=request_gate)
        self._map_store = Store(hass, 1,
            f"{DOMAIN}.{entry.entry_id}.location_fire_risk_map.{context.cache_identity}")
        self._normal_interval = _staggered_interval(f"{entry.entry_id}:{context.location_id}")
        self._consecutive_failures = 0
        super().__init__(hass, _LOGGER, config_entry=entry,
            name=f"{DOMAIN}_location_fire_risk_{context.location_id}",
            update_interval=self._normal_interval)

    @property
    def context(self) -> FireRiskRequestContext:
        return self._context

    async def _async_setup(self) -> None:
        import_scoped_map_cache(self.client, self.context, await self._map_store.async_load())

    def _defer(self, error: ForecastRequestDeferred) -> None:
        # Local waiting does not increment an upstream failure counter or issue
        # a legacy Home repair. It must not hold a coordinator update open.
        self.update_interval = min(timedelta(hours=1),
            max(timedelta(seconds=1), error.retry_after))

    async def _async_update_data(self) -> LocationFireRiskForecast:
        context = self.context
        try:
            forecast = await self.client.async_forecast(
                context.latitude, context.longitude, context.radius_km)
        except ForecastRequestDeferred as err:
            self._defer(err)
            raise UpdateFailed("Location forecast is waiting for provider cooldown") from err
        except FireRiskError as err:
            self._consecutive_failures += 1
            self.update_interval = _retry_interval(self._consecutive_failures, error=err)
            raise UpdateFailed(safe_fire_risk_reason(err)) from err

        self._consecutive_failures = 0
        self.update_interval = self._normal_interval
        bbox = map_bounds(context.latitude, context.longitude, context.radius_km)
        try:
            image = await self.client.async_map(bbox, forecast.days[0].valid_date)
            level, latitude, longitude = await self.hass.async_add_executor_job(
                analyze_risk_map, image, bbox,
                context.latitude, context.longitude, context.radius_km)
            forecast = replace(forecast, area_level=level,
                area_latitude=latitude, area_longitude=longitude)
        except ForecastRequestDeferred as err:
            self._defer(err)
        except FireRiskError as err:
            # Valid point data remains useful even if the optional map fails.
            self.update_interval = _retry_interval(1, error=err)
            _LOGGER.debug("Location forecast map unavailable: %s", safe_fire_risk_reason(err))
        else:
            if (cache := self.client.export_map_cache()) is not None:
                try:
                    await self._map_store.async_save(context.wrap_map_cache(cache))
                except OSError:
                    _LOGGER.warning("Could not persist location forecast map cache")
        return LocationFireRiskForecast(context, forecast)
