"""Immutable request geometry; does not schedule or assign forecast providers."""
from __future__ import annotations

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
