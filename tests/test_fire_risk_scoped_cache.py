"""Scoped map restore must enforce geometry and the original provider limits."""
from datetime import UTC, datetime, timedelta
from unittest.mock import Mock

import pytest

from custom_components.terralyra_ignis.fire_risk_cache import import_scoped_map_cache
from custom_components.terralyra_ignis.fire_risk_context import FireRiskRequestContext
from custom_components.terralyra_ignis.products.fire_risk import FireRiskClient, map_bounds


def setup_cache():
    context = FireRiskRequestContext("one", "eumetsat_lsa_saf_frmv3", "FRMv3", 47.5, 19, 25)
    source = FireRiskClient(object())
    source._map_cache_key = (map_bounds(47.5, 19, 25), datetime.now(UTC).date())
    source._map_cache_value = b"\x89PNG\r\n\x1a\ncache"
    source._map_cache_time = datetime.now(UTC)
    return context, context.wrap_map_cache(source.export_map_cache())


def test_scoped_cache_round_trip_and_legacy_not_accepted():
    context, payload = setup_cache()
    client = FireRiskClient(object())
    assert import_scoped_map_cache(client, context, payload)
    original = client._map_cache_value
    assert not import_scoped_map_cache(client, context, payload["provider_cache"])
    assert client._map_cache_value == original


@pytest.mark.parametrize("change", ["geometry", "expired", "invalid_date", "bytes", "future_age"])
def test_matching_identity_is_not_sufficient(change):
    context, payload = setup_cache()
    raw = payload["provider_cache"]
    if change == "geometry":
        raw["bounds"][0] += 0.000001
    elif change == "expired":
        raw["cached_at"] = (datetime.now(UTC) - timedelta(hours=25)).isoformat()
    elif change == "future_age":
        raw["cached_at"] = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
    elif change == "invalid_date":
        raw["valid_date"] = "invalid"
    else:
        raw["png"] = "not-base64"
    assert not import_scoped_map_cache(FireRiskClient(object()), context, payload)


def test_foreign_context_rejected_before_provider_import():
    context, payload = setup_cache()
    other = FireRiskRequestContext("two", context.provider, context.product, 47.5, 19, 25)
    client = Mock()
    assert not import_scoped_map_cache(client, other, payload)
    client.import_map_cache.assert_not_called()
