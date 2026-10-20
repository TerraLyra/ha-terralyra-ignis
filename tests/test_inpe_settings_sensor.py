"""Explicit opt-in, bounded states and unavailable-vs-empty display."""
from datetime import datetime, UTC
from unittest.mock import AsyncMock, patch
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from custom_components.terralyra_ignis.const import DOMAIN
from custom_components.terralyra_ignis.inpe_sensor import create_inpe_sensor
from custom_components.terralyra_ignis.derived_sources.inpe.settings import settings
from custom_components.terralyra_ignis.derived_sources.inpe.coordinator import State


def test_settings_require_explicit_valid_scope():
    assert settings({}) == (False, ())
    for opts in ({'inpe_enabled':True}, {'inpe_enabled':True,'inpe_states':['XX']},
                 {'inpe_enabled':True,'inpe_states':['AC','AC']},
                 {'inpe_enabled':True,'inpe_states':['AC','AM','BA','SP']}):
        with pytest.raises(ValueError): settings(opts)


async def test_disabled_never_creates_session(hass):
    entry=MockConfigEntry(domain=DOMAIN)
    with patch('custom_components.terralyra_ignis.inpe_sensor.async_get_clientsession') as session:
        assert create_inpe_sensor(hass,entry) is None
        session.assert_not_called()


async def test_display_empty_error_and_reload_reuse(hass):
    entry=MockConfigEntry(domain=DOMAIN,options={'inpe_enabled':True,'inpe_states':['AC']})
    sensor=create_inpe_sensor(hass,entry)
    assert not sensor.available
    assert create_inpe_sensor(hass,entry).owner is sensor.owner
    sensor.owner.state=State('success',(),datetime(2026,10,20,tzinfo=UTC))
    assert sensor.available and sensor.native_value == 0
    assert sensor.extra_state_attributes['coverage_complete'] is False
    receipt=sensor.extra_state_attributes['last_success_at']
    sensor.owner.state=State('error',(),sensor.owner.state.last_success,'retrieval_failed')
    assert not sensor.available and sensor.native_value is None
    assert sensor.extra_state_attributes['last_success_at'] == receipt
    sensor.owner.async_refresh=AsyncMock()
    await sensor.async_update()
    sensor.owner.async_refresh.assert_awaited_once()
