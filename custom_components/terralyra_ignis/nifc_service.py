"""Explicit administrator-only NIFC first-use action; never enables retrieval."""
import voluptuous as vol

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import SupportsResponse
from homeassistant.exceptions import ServiceValidationError, Unauthorized
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.service import async_register_admin_service

from .const import DOMAIN
from .official_sources.nifc.owner import get_nifc_owner

SERVICE_INITIALIZE_NIFC = 'initialize_nifc'


def register_nifc_initialization(hass):
    """Registration does not access storage or the provider."""
    def validate(call):
        # Unlike routine admin services, first-use intent requires an identified user.
        if not call.context.user_id:
            raise Unauthorized(context=call.context)
        entry = hass.config_entries.async_get_entry(call.data['config_entry_id'])
        if entry is None or entry.domain != DOMAIN or entry.state is not ConfigEntryState.LOADED:
            raise ServiceValidationError('Select a loaded TerraLyra IGNIS entry')

    def finish(status):
        runtime = hass.data.get(DOMAIN, {}).get('nifc_runtime')
        enabled = False
        if runtime is not None:
            enabled = runtime.enabled
            runtime.request_refresh()
        return {'status': status, 'retrieval_enabled': enabled, 'history_changed': False}

    async def initialize(call):
        validate(call)
        try:
            status = await get_nifc_owner(hass).async_initialize(confirmed_new=True)
        except (ValueError, OSError) as err:
            raise ServiceValidationError(
                'NIFC initialization could not complete. Review the stored initialization '
                'and cooldown state; do not delete them or use initialization as a reset.'
            ) from err
        return finish(status)

    async_register_admin_service(
        hass, DOMAIN, SERVICE_INITIALIZE_NIFC, initialize,
        schema=vol.Schema({
            vol.Required('config_entry_id'): cv.string,
            vol.Required('confirm_first_use'): vol.All(bool, vol.In([True])),
        }),
        supports_response=SupportsResponse.ONLY,
    )

    async def recover(call):
        validate(call)
        try:
            await get_nifc_owner(hass).async_recover()
        except (ValueError, OSError) as err:
            raise ServiceValidationError(
                'NIFC recovery requires valid existing storage and a known wait bound. '
                'Wait for pending writes. Missing/corrupt data or an unknown/unbounded '
                'server pause cannot be reset; restore a validated backup or investigate the source.'
            ) from err
        return finish('recovered')

    async_register_admin_service(
        hass, DOMAIN, 'recover_nifc', recover,
        schema=vol.Schema({
            vol.Required('config_entry_id'): cv.string,
            vol.Required('confirm_review'): vol.All(bool, vol.In([True])),
        }),
        supports_response=SupportsResponse.ONLY,
    )
