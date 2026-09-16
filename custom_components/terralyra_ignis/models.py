"""Provider-neutral active-fire data models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any

from .basic_models import FireDetection, ProviderSnapshot, ProviderStatus


class FireLifecycle(StrEnum):
    """Lifecycle state of one tracked fire incident."""

    NEW = "new"
    CONTINUING = "continuing"
    INACTIVE = "inactive"
    ENDED = "ended"


class MetricTrend(StrEnum):
    """Trend direction for FRP and detection activity."""

    INCREASING = "increasing"
    STABLE = "stable"
    DECREASING = "decreasing"
    UNKNOWN = "unknown"


class DistanceTrend(StrEnum):
    """Trend of detected activity relative to a monitored reference location."""

    APPROACHING = "approaching"
    STABLE = "stable"
    RECEDING = "receding"
    UNKNOWN = "unknown"


class ConfirmationLevel(StrEnum):
    """Explainable independent-source confirmation state."""

    DISABLED = "disabled"
    NOT_AVAILABLE = "not_available"
    NO_ACTIVE_FIRE = "no_active_fire"
    SINGLE_SOURCE = "single_source"
    MULTI_SOURCE = "multi_source"


@dataclass(frozen=True, slots=True)
class IncidentLocationMatch:
    """Relevance of one incident to one locally monitored location."""

    incident_id: str
    location_id: str
    location_name: str
    distance_km: float
    radius_km: float
    direction: str
    inside_radius: bool
    distance_trend: DistanceTrend = DistanceTrend.UNKNOWN
    minimum_distance_km: float | None = None

    def attrs(self) -> dict[str, str | float | bool]:
        """Compatibility adapter for the existing HA attribute contract."""
        from .ha.attributes import location_attributes

        return location_attributes(self)


@dataclass(slots=True)
class FireCluster:
    """A spatial group of fire detections from one provider snapshot."""

    latitude: float
    longitude: float
    distance_km: float
    confidence: float
    frp_mw: float
    acquired: datetime
    pixel_count: int
    track_id: str | None = None
    family_id: str | None = None
    source_track_ids: tuple[str, ...] = ()
    incident_extent_km: float | None = None
    peak_frp_mw: float | None = None
    place_name: str | None = None
    nearest_settlement: str | None = None
    location_description: str | None = None
    place_attribution: str | None = None
    lifecycle: FireLifecycle | None = None
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    minimum_distance_km: float | None = None
    maximum_frp_mw: float | None = None
    maximum_pixel_count: int | None = None
    detections_total: int | None = None
    maximum_confidence: float | None = None
    frp_trend: MetricTrend | None = None
    activity_trend: MetricTrend | None = None
    distance_trend: DistanceTrend | None = None
    trend_samples: int | None = None
    trend_window_minutes: float | None = None
    confirmation_level: ConfirmationLevel = ConfirmationLevel.SINGLE_SOURCE
    providers: tuple[str, ...] = ()
    satellites: tuple[str, ...] = ()
    corroborating_detections: int = 0
    source_url: str | None = None
    location_matches: tuple[IncidentLocationMatch, ...] = ()

    def attrs(self) -> dict[str, Any]:
        """Compatibility adapter for the existing HA attribute contract."""
        from .ha.attributes import fire_attributes

        return fire_attributes(self)
