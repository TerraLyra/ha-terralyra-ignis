"""One lazy NIFC client and cooldown owner per Home Assistant instance."""
import asyncio

from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import Store

from ...const import DOMAIN
from .client import NifcClient
from .stored_coordinator import NifcStoredCoordinator

STORE_KEY = f'{DOMAIN}.nifc_cooldown'
DATA_KEY = 'nifc_owner'


class NifcOwner:
    """Explicit calls only; constructing an owner performs no storage/network I/O.

    An established valid cooldown store is required. First-install initialization,
    deliberate recovery and entity scheduling are separate lifecycle operations.
    """
    def __init__(self, session, store):
        self.client = NifcClient(session)
        self.coordinator = NifcStoredCoordinator(store, fetcher=self.client.async_fetch)
        self._lock = asyncio.Lock()

    @property
    def state(self):
        return self.coordinator.state

    def diagnostics(self):
        return self.coordinator.diagnostics()

    async def async_refresh(self, *, enabled=False, has_enabled_locations=False):
        if type(enabled) is not bool or type(has_enabled_locations) is not bool:
            raise ValueError('Explicit boolean eligibility required')
        if not enabled or not has_enabled_locations or self._lock.locked():
            return 'skipped'
        # HA calls on a single event loop; no await between guard and acquisition.
        async with self._lock:
            await self.coordinator.setup()
            return await self.coordinator.refresh(enabled=True)


def get_nifc_owner(hass):
    """Reuse the same owner across entries and repeated integration setup."""
    data = hass.data.setdefault(DOMAIN, {})
    if DATA_KEY not in data:
        data[DATA_KEY] = NifcOwner(async_get_clientsession(hass), Store(hass, 1, STORE_KEY))
    return data[DATA_KEY]
