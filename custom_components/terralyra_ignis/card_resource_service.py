"""Explicit administrator-only optional card registration."""
import asyncio
import hashlib
from pathlib import Path
import voluptuous as vol
from homeassistant.components.lovelace.const import LOVELACE_DATA
from homeassistant.components.lovelace.resources import ResourceStorageCollection
from homeassistant.core import SupportsResponse
from homeassistant.exceptions import ServiceValidationError, Unauthorized
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.service import async_register_admin_service
from .card_resource_plan import CARDS, plan_card_resource
from .const import DOMAIN


def register_card_resource_service(hass):
    """No resource loading or writes until an administrator invokes the action."""
    lock = asyncio.Lock()

    async def handle(call):
        if not call.context.user_id:
            raise Unauthorized(context=call.context)
        async with lock:
            data = hass.data.get(LOVELACE_DATA)
            if data is None:
                raise ServiceValidationError(translation_domain=DOMAIN, translation_key='card_resources_unavailable')
            collection = data.resources
            await collection.async_get_info()
            try:
                items = collection.async_items()
                plan = plan_card_resource(call.data['card'], items)
            except ValueError as err:
                raise ServiceValidationError(translation_domain=DOMAIN, translation_key='card_resources_review') from err
            plan['changed'] = False
            if data.resource_mode != 'storage' or not isinstance(collection, ResourceStorageCollection):
                return {**plan, 'status': 'yaml_manual_setup'}
            if call.data['refresh_existing']:
                if plan['status'] != 'already_registered':
                    return plan
                item = next(item for item in items if item['url'] == plan['matching_urls'][0])
                # Hash bundled public bytes off the event loop. No network or user files.
                def versioned_url():
                    content = (Path(__file__).parent / 'www' / CARDS[call.data['card']]).read_bytes()
                    return plan['url'] + '?v=' + hashlib.sha256(content).hexdigest()[:16]
                url = await hass.async_add_executor_job(versioned_url)
                if item['url'] == url:
                    return {**plan, 'url': url}
                await collection.async_update_item(item['id'], {'url': url})
                return {**plan, 'url': url, 'status': 'refreshed', 'changed': True}
            if not call.data['confirm_no_renamed_copy'] or plan['status'] != 'confirm_no_renamed_copy':
                return plan
            await collection.async_create_item({'url': plan['url'], 'res_type': 'module'})
            return {**plan, 'status': 'registered', 'changed': True}

    async_register_admin_service(hass, DOMAIN, 'register_dashboard_card', handle,
        schema=vol.Schema({vol.Required('card'): vol.In(CARDS),
            vol.Optional('confirm_no_renamed_copy', default=False): cv.boolean,
            vol.Optional('refresh_existing', default=False): cv.boolean}),
        supports_response=SupportsResponse.ONLY)
