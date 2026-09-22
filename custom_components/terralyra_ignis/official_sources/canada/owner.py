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

    state = None
    initialization_status = 'not_checked'
    problem = None

    async def async_refresh(self, *, enabled=False, has_enabled_locations=False, allow_uninitialized=False):
        if type(enabled) is not bool or type(has_enabled_locations) is not bool:
            raise ValueError('Explicit eligibility required')
        if not enabled or not has_enabled_locations or self.lock.locked():
            return
        try:
            if not await self.store.async_is_initialized():
                self.initialization_status = 'required'
                return
            self.state = await self.refresh()
            self.initialization_status = 'ready'
            self.problem = None
        except (OSError, ValueError):
            self.problem = 'storage_review_required'
            raise

    def diagnostics(self):
        return {'problem': self.problem or self.store.problem,
                'storage_pending': self.store.pending,
                'storage_review_required': self.store.blocked,
                'initialization_status': self.initialization_status}

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
