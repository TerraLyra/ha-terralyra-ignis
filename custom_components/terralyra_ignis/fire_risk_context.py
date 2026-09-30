"""Immutable request geometry; does not schedule or assign forecast providers."""
from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass

from .products.fire_risk import FireRiskError


@dataclass(frozen=True, slots=True)
class FireRiskRequestContext:
    """Explicit identity and geometry for a single forecast request.

    The legacy Home identity denotes HA's home coordinate, not a monitored
    location named Home. This internal context is not a public entity binding.
    Provider coverage validation remains the provider's responsibility.
    """

    location_id: str
    provider: str
    product: str
    latitude: float
    longitude: float
    radius_km: float

    def __post_init__(self) -> None:
        for value in (self.location_id, self.provider, self.product):
            if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", value):
                raise FireRiskError("Invalid forecast request identity")
        for value, lower, upper in (
            (self.latitude, -90, 90),
            (self.longitude, -180, 180),
            (self.radius_km, 1, 500),
        ):
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or not lower <= value <= upper
            ):
                raise FireRiskError("Invalid forecast request geometry")

    @property
    def cache_identity(self) -> str:
        """Opaque exact-geometry identity; independent of display name/order.

        Normalize numeric representation only (including signed zero), never
        round coordinates. Entry separation remains the storage owner's job.
        """
        geometry = [float(v) if v != 0 else 0.0 for v in (
            self.latitude, self.longitude, self.radius_km
        )]
        payload = [self.location_id, self.provider, self.product, *geometry]
        return hashlib.sha256(json.dumps(payload, separators=(",", ":")).encode()).hexdigest()

    def wrap_map_cache(self, payload: dict) -> dict:
        """Add context provenance to a provider-validated map cache payload."""
        return {"context_schema": 1, "context_identity": self.cache_identity,
                "provider_cache": payload}

    def unwrap_map_cache(self, payload: object) -> dict | None:
        """Reject legacy, mismatched or malformed scoped cache envelopes.

        The provider must still validate bounds, date, age, size and bytes before
        use. This identity check alone is not a cache validity guarantee.
        """
        if (
            not isinstance(payload, dict)
            or type(payload.get("context_schema")) is not int
            or payload["context_schema"] != 1
            or payload.get("context_identity") != self.cache_identity
            or not isinstance(payload.get("provider_cache"), dict)
        ):
            return None
        return payload["provider_cache"]
