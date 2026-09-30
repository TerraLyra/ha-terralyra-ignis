"""Context-scoped cache boundary for future multi-location forecast clients."""
from __future__ import annotations

from .fire_risk_context import FireRiskRequestContext
from .fire_risk_coverage import FIRE_RISK_PROVIDER_LSA_SAF
from .products.fire_risk import PRODUCT_ID, FireRiskClient, FireRiskError, map_bounds


def import_scoped_map_cache(
    client: FireRiskClient, context: FireRiskRequestContext, payload: object,
) -> bool:
    """Validate scope and expected geometry before provider-level cache import.

    Must be used with a separate client per context. Invalid input does not erase
    an existing cache. Legacy Home continues using its existing import path.
    """
    if context.provider != FIRE_RISK_PROVIDER_LSA_SAF or context.product != PRODUCT_ID:
        return False
    raw = context.unwrap_map_cache(payload)
    if raw is None:
        return False
    try:
        expected = map_bounds(context.latitude, context.longitude, context.radius_km)
        bounds = raw.get("bounds")
        if (
            not isinstance(bounds, list) or len(bounds) != 4
            or any(isinstance(v, bool) or not isinstance(v, (int, float)) for v in bounds)
            or tuple(bounds) != expected
        ):
            return False
    except FireRiskError:
        return False
    return client.import_map_cache(raw)
