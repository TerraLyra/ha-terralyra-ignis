"""Administrator-only first-use initialization. Never resets existing state."""
import voluptuous as vol
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import SupportsResponse
from homeassistant.exceptions import ServiceValidationError, Unauthorized
from homeassistant.helpers.service import async_register_admin_service
from .const import DOMAIN
from .tasalert_runtime import get_tasalert_runtime


def register_tasalert_initialization(hass):
    async def initialize(call):
        if not call.context.user_id:raise Unauthorized(context=call.context)
        entry=hass.config_entries.async_get_entry(call.data['config_entry_id'])
        if entry is None or entry.domain!=DOMAIN or entry.state is not ConfigEntryState.LOADED:
            raise ServiceValidationError('Select a loaded TerraLyra IGNIS entry')
        runtime=get_tasalert_runtime(hass)
        try:await runtime.owner.async_load(confirmed_new=True)
        except (OSError,ValueError) as error:
            raise ServiceValidationError('TasALERT storage requires review; initialization cannot reset it') from error
        runtime.notify()
        runtime.request_refresh()
        return {'status':'initialized','retrieval_enabled':runtime.enabled}
    async_register_admin_service(hass,DOMAIN,'initialize_tasalert',initialize,
        schema=vol.Schema({vol.Required('config_entry_id'):str,
                          vol.Required('confirm_first_use'):vol.All(bool,vol.In([True]))}),
        supports_response=SupportsResponse.ONLY)

    async def recover(call):
        if not call.context.user_id:
            raise Unauthorized(context=call.context)
        entry = hass.config_entries.async_get_entry(call.data['config_entry_id'])
        if entry is None or entry.domain != DOMAIN or entry.state is not ConfigEntryState.LOADED:
            raise ServiceValidationError('Select a loaded TerraLyra IGNIS entry')
        runtime = get_tasalert_runtime(hass)
        try:
            await runtime.owner.async_recover()
        except (OSError, ValueError) as error:
            raise ServiceValidationError('TasALERT recovery requires completed I/O and a valid existing store') from error
        runtime.notify()
        return {'status': 'recovered', 'history_changed': False}

    async_register_admin_service(hass, DOMAIN, 'recover_tasalert', recover,
        schema=vol.Schema({vol.Required('config_entry_id'): str,
                          vol.Required('confirm_review'): vol.All(bool, vol.In([True]))}),
        supports_response=SupportsResponse.ONLY)
