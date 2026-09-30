"""Explicitly bound per-location FRMv3 forecasts; legacy Home IDs stay intact."""
from datetime import UTC, datetime, time, timedelta

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.event import async_track_point_in_utc_time
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .products.fire_risk import WMS_URL


class LocationFireRiskSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "location_fire_risk"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["low", "moderate", "high", "very_high", "extreme", "unknown"]
    _attr_icon = "mdi:pine-tree-fire"

    def __init__(self, entry, coordinator, location_name):
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_location_fire_risk_{coordinator.context.location_id}"
        self._attr_translation_placeholders = {"location_name": location_name}
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry.entry_id)})
        self._cancel_midnight = None

    def _current(self):
        result = self.coordinator.data
        if (not self.coordinator.last_update_success or result is None
                or result.context != self.coordinator.context or not result.forecast.days
                or result.forecast.days[0].valid_date != datetime.now(UTC).date()):
            return None
        return result.forecast

    @property
    def available(self):
        return super().available and self._current() is not None

    @property
    def native_value(self):
        value = self._current()
        return value.days[0].risk if value else None

    @property
    def extra_state_attributes(self):
        context = self.coordinator.context
        attrs = {
            "scope": "monitored_location", "location_id": context.location_id,
            "latitude": context.latitude, "longitude": context.longitude,
            "forecast_radius_km": context.radius_km,
            "provider": context.provider, "product": context.product,
            "source_url": WMS_URL, "attribution": "EUMETSAT / LSA SAF, CC BY 4.0",
            "forecast": [],
        }
        if (value := self._current()) is not None:
            attrs.update({
                "risk_level": value.days[0].level,
                "sample_latitude": value.latitude, "sample_longitude": value.longitude,
                "generated_at": value.generated_at.isoformat(),
                "time_semantics": "retrieval_time_not_issuance",
                "valid_date": value.days[0].valid_date.isoformat(),
                "forecast": [{"date": day.valid_date.isoformat(), "risk": day.risk,
                              "level": day.level} for day in value.days],
            })
        return attrs

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self._schedule_midnight()

    @callback
    def _schedule_midnight(self):
        tomorrow = datetime.now(UTC).date() + timedelta(days=1)
        self._cancel_midnight = async_track_point_in_utc_time(
            self.hass, self._midnight, datetime.combine(tomorrow, time(), UTC))

    @callback
    def _midnight(self, now):
        self.async_write_ha_state()
        self._schedule_midnight()

    async def async_will_remove_from_hass(self):
        if self._cancel_midnight is not None:
            self._cancel_midnight()
            self._cancel_midnight = None
        await super().async_will_remove_from_hass()
