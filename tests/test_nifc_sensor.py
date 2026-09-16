"""Passive diagnostic entities must never activate the NIFC source."""
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
import math

import pytest
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.storage import Store

from custom_components.terralyra_ignis.nifc_sensor import NifcDiagnosticSensor
from custom_components.terralyra_ignis.official_sources.nifc.owner import get_nifc_owner
from custom_components.terralyra_ignis.official_sources.nifc.refresh import RefreshState
from custom_components.terralyra_ignis.official_sources.nifc.query import FetchResult


async def test_passive_sensor_never_initializes_or_requests(hass):
    owner = get_nifc_owner(hass)
    sensor = NifcDiagnosticSensor(SimpleNamespace(entry_id='one'), owner)
    with patch.object(Store, 'async_load', new_callable=AsyncMock) as load, patch.object(Store, 'async_save', new_callable=AsyncMock) as save, patch.object(owner, 'async_refresh', new_callable=AsyncMock) as refresh:
        await sensor.async_update()
        assert sensor.native_value == 'not_requested'
        assert sensor.extra_state_attributes['retrieval_enabled'] is False
        load.assert_not_awaited()
        save.assert_not_awaited()
        refresh.assert_not_awaited()
    assert sensor.entity_registry_enabled_default is False
    assert sensor.entity_category == EntityCategory.DIAGNOSTIC
    second = NifcDiagnosticSensor(SimpleNamespace(entry_id='two'), owner)
    assert sensor.unique_id != second.unique_id
    assert sensor.device_info['identifiers'] != second.device_info['identifiers']


@pytest.mark.parametrize('problem,state,expected', [
    ('review_required', None, 'review_required'),
    ('storage_load_failed', None, 'review_required'),
    (None, RefreshState(next_attempt_at=math.inf), 'review_required'),
    (None, RefreshState(next_attempt_at=200), 'waiting'),
    (None, RefreshState(), 'not_requested'),
    ('refresh_failed_transient', RefreshState(next_attempt_at=200), 'waiting'),
    ('refresh_failed_rate_limited', RefreshState(next_attempt_at=200), 'waiting'),
    (None, RefreshState(last_success=FetchResult((),1,1,'terminal_reported'), status='retrieved'), 'available'),
    ('refresh_failed_transient', RefreshState(last_success=FetchResult((),1,1,'terminal_reported'), status='refresh_failed_transient'), 'retained_response'),
])
def test_status_is_retrieval_health_only(problem, state, expected):
    owner = SimpleNamespace(state=state, diagnostics=lambda: {'problem': problem})
    sensor = NifcDiagnosticSensor(SimpleNamespace(entry_id='one'), owner)
    with patch('custom_components.terralyra_ignis.nifc_sensor.time.monotonic', return_value=100):
        assert sensor.native_value == expected
    assert sensor.extra_state_attributes['national_completeness'] == 'not_established'
    assert 'active_fire_count' not in sensor.extra_state_attributes
