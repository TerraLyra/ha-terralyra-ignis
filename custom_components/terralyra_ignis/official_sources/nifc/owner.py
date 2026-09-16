"""One lazy NIFC client and cooldown owner per Home Assistant instance."""
import asyncio

from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import Store

from ...const import DOMAIN
from .client import NifcClient
from .stored_coordinator import NifcStoredCoordinator, _settled_save
from .coordinator import restore_checkpoint

STORE_KEY = f'{DOMAIN}.nifc_cooldown'
DATA_KEY = 'nifc_owner'
INITIALIZATION_KEY = f'{DOMAIN}.nifc_initialization'


class NifcOwner:
    """Explicit calls only; constructing an owner performs no storage/network I/O.

    An established valid cooldown store is required. First-install initialization,
    deliberate recovery and entity scheduling are separate lifecycle operations.
    """
    def __init__(self, session, store, initialization_store=None):
        self._store = store
        self._initialization_store = initialization_store
        self.client = NifcClient(session)
        self.coordinator = NifcStoredCoordinator(store, fetcher=self.client.async_fetch)
        self._lock = asyncio.Lock()

    @property
    def state(self):
        return self.coordinator.state

    def diagnostics(self):
        return self.coordinator.diagnostics()

    async def async_initialize(self, *, confirmed_new=False):
        """Explicit first-use operation; never overwrite an existing cooldown.

        Caller must establish first-use intent independently. Absence of both stores
        cannot distinguish a new install from external deletion; it is not consent.
        An interrupted transaction remains blocked for deliberate recovery.
        """
        if type(confirmed_new) is not bool:
            raise ValueError('Explicit boolean first-use confirmation required')
        if self._initialization_store is None:
            raise RuntimeError('Initialization ledger required')
        async with self._lock:
            ledger = await self._initialization_store.async_load()
            saved = await self._store.async_load()
            if ledger is not None and ledger != {'version': 1, 'phase': 'ready'}:
                raise ValueError('Initialization requires review')
            if saved is not None:
                restore_checkpoint(saved, now=0)
                # Existing valid cooldown is adopted, never reset or shortened.
                if ledger is None:
                    await _settled_save(self._initialization_store, {'version': 1, 'phase': 'ready'})
                return 'existing'
            if ledger is not None:
                raise ValueError('Established cooldown state is missing')
            if not confirmed_new:
                raise ValueError('First-use confirmation required')
            await _settled_save(self._initialization_store, {'version': 1, 'phase': 'started'})
            await _settled_save(self._store, {'version': 1, 'wait_seconds': 0, 'failures': 0})
            await _settled_save(self._initialization_store, {'version': 1, 'phase': 'ready'})
            return 'initialized'

    async def async_refresh(self, *, enabled=False, has_enabled_locations=False):
        if type(enabled) is not bool or type(has_enabled_locations) is not bool:
            raise ValueError('Explicit boolean eligibility required')
        if not enabled or not has_enabled_locations or self._lock.locked():
            return 'skipped'
        # HA calls on a single event loop; no await between guard and acquisition.
        async with self._lock:
            if self._initialization_store is not None:
                ledger = await self._initialization_store.async_load()
                if ledger is not None and ledger != {"version": 1, "phase": "ready"}:
                    raise ValueError("Initialization requires review")
            await self.coordinator.setup()
            return await self.coordinator.refresh(enabled=True)


def get_nifc_owner(hass):
    """Reuse the same owner across entries and repeated integration setup."""
    data = hass.data.setdefault(DOMAIN, {})
    if DATA_KEY not in data:
        data[DATA_KEY] = NifcOwner(async_get_clientsession(hass), Store(hass, 1, STORE_KEY),
                                    Store(hass, 1, INITIALIZATION_KEY))
    return data[DATA_KEY]
