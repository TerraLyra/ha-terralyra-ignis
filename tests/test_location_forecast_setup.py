"""Entry wiring shares provider pacing without implicit location opt-in."""
import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest
from homeassistant.exceptions import ConfigEntryError

from custom_components.terralyra_ignis import async_setup_entry
from custom_components.terralyra_ignis.core.locations import MonitoredLocation
from custom_components.terralyra_ignis.fire_risk_planning import CONF_LOCATION_FORECASTS
from custom_components.terralyra_ignis.fire_risk_request_state import get_forecast_request_gate


@pytest.mark.parametrize('enabled', [False, True])
async def test_setup_passes_same_gate_to_home_and_location_runtime(hass, enabled):
    import custom_components.terralyra_ignis as integration
    location = MonitoredLocation('cabin', 'Cabin', 47., 19., 300., True, 'manual')
    entry = Mock(entry_id='entry', options={'resolve_place_names': False,
        CONF_LOCATION_FORECASTS: [{'location_id': 'cabin', 'enabled': True, 'radius_km': 40}] if enabled else []}, data={})
    tasks = []
    def create(hass, coro, name):
        task = asyncio.create_task(coro)
        tasks.append(task)
        return task
    entry.async_create_background_task.side_effect = create
    active = Mock(async_config_entry_first_refresh=AsyncMock())
    home = Mock(async_refresh=AsyncMock())
    runtime = Mock(close=AsyncMock())
    with patch.object(integration, 'resolve_monitored_locations', return_value=(location,)), \
         patch.object(integration, 'resolve_monitoring_center'), \
         patch.object(integration, 'build_provider_pool', return_value=(Mock(), ())), \
         patch.object(integration, 'async_sync_coverage_issue'), \
         patch.object(integration, 'IgnisCoordinator', return_value=active), \
         patch.object(integration, 'FireRiskCoordinator', return_value=home), \
         patch.object(integration, 'LandSurfaceTemperatureCoordinator'), \
         patch.object(integration, 'FireRiskClient') as client, \
         patch.object(integration, 'LocationForecastRuntime', return_value=runtime) as owner, \
         patch.object(hass.config_entries, 'async_forward_entry_setups', new=AsyncMock()):
        assert await async_setup_entry(hass, entry)
        assert client.call_args.kwargs['request_gate'] is owner.call_args.args[-1]
        assert len(owner.call_args.args[-2]) == int(enabled)
        entry.async_on_unload.assert_called_with(runtime.close)
        runtime.start.assert_called_once()
        assert entry.runtime_data.location_forecasts is runtime
        await asyncio.gather(*tasks)


async def test_invalid_options_fail_before_network(hass):
    entry = Mock(options={CONF_LOCATION_FORECASTS: 'invalid'})
    with patch('custom_components.terralyra_ignis.async_get_clientsession') as session:
        with pytest.raises(ConfigEntryError):
            await async_setup_entry(hass, entry)
        session.assert_not_called()


def test_one_gate_per_installation(hass):
    assert get_forecast_request_gate(hass) is get_forecast_request_gate(hass)
