"""Explicit administrator-only Canada first-use action; never enables retrieval."""
import voluptuous as vol

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import SupportsResponse
from homeassistant.exceptions import ServiceValidationError, Unauthorized
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.service import async_register_admin_service

from .const import DOMAIN
from .official_sources.canada.owner import get_canada_owner

SERVICE_INITIALIZE_Canada = 'initialize_canada'


def register_canada_initialization(hass):
    """Registration does not access storage or the provider."""
    def validate(call):
        # Unlike routine admin services, first-use intent requires an identified user.
        if not call.context.user_id:
            raise Unauthorized(context=call.context)
        entry = hass.config_entries.async_get_entry(call.data['config_entry_id'])
        if entry is None or entry.domain != DOMAIN or entry.state is not ConfigEntryState.LOADED:
            raise ServiceValidationError('Select a loaded TerraLyra IGNIS entry')

    def finish(status):
        # Preparation only: the Canada runtime is not registered yet.
        return {'status': status, 'retrieval_enabled': False, 'history_changed': False}

    async def initialize(call):
        validate(call)
        try:
            status = await get_canada_owner(hass).async_initialize(confirmed_new=True)
        except (ValueError, OSError) as err:
            raise ServiceValidationError(
                'Canada initialization could not complete. Review the stored initialization '
                'and cooldown state; do not delete them or use initialization as a reset.'
            ) from err
        return finish(status)

    async_register_admin_service(
        hass, DOMAIN, SERVICE_INITIALIZE_Canada, initialize,
        schema=vol.Schema({
            vol.Required('config_entry_id'): cv.string,
            vol.Required('confirm_first_use'): vol.All(bool, vol.In([True])),
        }),
        supports_response=SupportsResponse.ONLY,
    )

    async def recover(call):
        validate(call)
        try:
            await get_canada_owner(hass).async_recover(confirmed_review=True)
        except (ValueError, OSError) as err:
            raise ServiceValidationError(
                'Canada recovery requires valid existing storage and a known wait bound. '
                'Wait for pending writes. Missing/corrupt data or an unknown/unbounded '
                'server pause cannot be reset; restore a validated backup or investigate the source.'
            ) from err
        return finish('recovered')

    async_register_admin_service(
        hass, DOMAIN, 'recover_canada', recover,
        schema=vol.Schema({
            vol.Required('config_entry_id'): cv.string,
            vol.Required('confirm_review'): vol.All(bool, vol.In([True])),
        }),
        supports_response=SupportsResponse.ONLY,
    )
