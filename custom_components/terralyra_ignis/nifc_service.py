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
    async def initialize(call):
        # Unlike routine admin services, first-use intent requires an identified user.
        if not call.context.user_id:
            raise Unauthorized(context=call.context)
        entry = hass.config_entries.async_get_entry(call.data['config_entry_id'])
        if entry is None or entry.domain != DOMAIN or entry.state is not ConfigEntryState.LOADED:
            raise ServiceValidationError('Select a loaded TerraLyra IGNIS entry')
        try:
            status = await get_nifc_owner(hass).async_initialize(confirmed_new=True)
        except (ValueError, OSError) as err:
            raise ServiceValidationError(
                'NIFC initialization could not complete. Review the stored initialization '
                'and cooldown state; do not delete them or use initialization as a reset.'
            ) from err
        return {'status': status, 'retrieval_enabled': False, 'history_changed': False}

    async_register_admin_service(
        hass, DOMAIN, SERVICE_INITIALIZE_NIFC, initialize,
        schema=vol.Schema({
            vol.Required('config_entry_id'): cv.string,
            vol.Required('confirm_first_use'): vol.All(bool, vol.In([True])),
        }),
        supports_response=SupportsResponse.ONLY,
    )
