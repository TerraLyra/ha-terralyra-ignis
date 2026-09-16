"""Public observation value objects, with no HA or I/O dependencies."""
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

__all__ = ["FireDetection", "ProviderSnapshot", "ProviderStatus"]

class ProviderStatus(StrEnum):
    """Availability state reported by an active-fire provider."""

    INITIALIZING = "initializing"
    AVAILABLE = "available"
    DELAYED = "delayed"
    NO_PRODUCT = "no_product"
    OUTAGE = "outage"
    AUTH_ERROR = "auth_error"


@dataclass(frozen=True, slots=True)
class FireDetection:
    """One provider-normalized satellite fire detection."""

    provider: str
    satellite: str
    product: str
    timestamp: datetime
    latitude: float
    longitude: float
    frp_mw: float | None = None
    frp_uncertainty_mw: float | None = None
    confidence: float | None = None
    classification: str | int | None = None
    quality: str | int | None = None
    fire_temperature_k: float | None = None
    fire_area_km2: float | None = None
    temporal_filtered: bool | None = None
    source_resolution_km: float | None = None
    source_detection_id: str | None = None
    # Distinct feeds produced by the same algorithm/provider family must not be
    # counted as independent confirmation. When omitted, ``provider`` remains
    # the family identifier for backwards compatibility.
    source_family: str | None = None


@dataclass(frozen=True, slots=True)
class ProviderSnapshot:
    """One complete provider product normalized for common processing."""

    provider: str
    satellite: str
    product: str
    product_timestamp: datetime
    received_timestamp: datetime
    status: ProviderStatus
    source_url: str
    filename: str
    detections: tuple[FireDetection, ...]


