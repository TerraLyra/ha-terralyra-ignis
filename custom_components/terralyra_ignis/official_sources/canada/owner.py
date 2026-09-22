"""Lazy Canada owner; not registered by integration setup yet."""
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import Store

from ...const import DOMAIN
from .controller import Controller
from .ha_storage import CanadaStore

STORE_KEY = f'{DOMAIN}.canada_state'
DATA_KEY = 'canada_owner'


class CanadaOwner(Controller):
    """Serialize admin operations with refresh; no automatic activation."""

    async def async_initialize(self, *, confirmed_new=False):
        async with self.lock:
            return await self.store.async_initialize(confirmed_new=confirmed_new)

    async def async_recover(self, *, confirmed_review=False):
        async with self.lock:
            return await self.store.async_recover(confirmed_review=confirmed_review,
                                                 now=self.clock())


def get_canada_owner(hass):
    """Share one controller and dedicated store across config entries."""
    data = hass.data.setdefault(DOMAIN, {})
    if DATA_KEY not in data:
        data[DATA_KEY] = CanadaOwner(None, async_get_clientsession(hass),
                                  store=CanadaStore(Store(hass, 1, STORE_KEY),
                                      create_task=hass.async_create_background_task))
    return data[DATA_KEY]
