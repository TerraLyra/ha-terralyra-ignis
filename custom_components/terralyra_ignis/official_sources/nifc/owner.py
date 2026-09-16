"""One lazy NIFC client and cooldown owner per Home Assistant instance."""
import asyncio
from functools import partial

from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import Store

from ...const import DOMAIN
from .client import NifcClient
from .stored_coordinator import NifcStoredCoordinator, _settled_save
from .coordinator import restore_checkpoint
from .storage import GuardedStore

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
        self.coordinator = NifcStoredCoordinator(store, fetcher=partial(self.client.async_fetch, inventory=True))
        self._lock = asyncio.Lock()
        self._ledger_problem = None
        self.initialization_status = "not_checked"

    @property
    def state(self):
        return self.coordinator.state

    def diagnostics(self):
        diagnostics = self.coordinator.diagnostics()
        if self._ledger_problem is not None:
            diagnostics['problem'] = self._ledger_problem
        stores = (self._store, self._initialization_store)
        diagnostics['storage_pending'] = any(getattr(store, 'pending', False) for store in stores)
        diagnostics['storage_review_required'] = any(getattr(store, 'blocked', False) for store in stores)
        if diagnostics['storage_review_required']:
            diagnostics['problem'] = 'storage_save_failed'
        diagnostics['initialization_status'] = self.initialization_status
        diagnostics['in_flight'] = self._lock.locked() or diagnostics['in_flight']
        return diagnostics

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
                self.initialization_status = 'ready'
                return 'existing'
            if ledger is not None:
                raise ValueError('Established cooldown state is missing')
            if not confirmed_new:
                raise ValueError('First-use confirmation required')
            await _settled_save(self._initialization_store, {'version': 1, 'phase': 'started'})
            await _settled_save(self._store, {'version': 1, 'wait_seconds': 0, 'failures': 0})
            await _settled_save(self._initialization_store, {'version': 1, 'phase': 'ready'})
            self.initialization_status = 'ready'
            return 'initialized'

    async def async_refresh(self, *, enabled=False, has_enabled_locations=False, allow_uninitialized=False):
        if type(enabled) is not bool or type(has_enabled_locations) is not bool:
            raise ValueError('Explicit boolean eligibility required')
        if not enabled or not has_enabled_locations or self._lock.locked():
            return 'skipped'
        # HA calls on a single event loop; no await between guard and acquisition.
        async with self._lock:
            if self._initialization_store is not None:
                try:
                    ledger = await self._initialization_store.async_load()
                except Exception:
                    self._ledger_problem = 'storage_load_failed'
                    raise
                if ledger is None and allow_uninitialized and self.state is None:
                    if await self._store.async_load() is None:
                        self.initialization_status = 'required'
                        return 'not_initialized'
                if ledger is not None and ledger != {"version": 1, "phase": "ready"}:
                    self._ledger_problem = 'review_required'
                    raise ValueError("Initialization requires review")
            self._ledger_problem = None
            await self.coordinator.setup()
            self.initialization_status = "ready"
            return await self.coordinator.refresh(enabled=True)


    async def async_recover(self):
        """Called only after explicit admin review; no missing-state reset."""
        async with self._lock:
            stores = (self._store, self._initialization_store)
            if any(getattr(store, 'pending', False) for store in stores):
                raise OSError('Storage still pending')
            for store in stores:
                if isinstance(store, GuardedStore):
                    store.allow_review()
            if self._initialization_store is None:
                raise ValueError('Initialization ledger required')
            ledger = await self._initialization_store.async_load()
            if ledger not in ({'version': 1, 'phase': 'ready'}, {'version': 1, 'phase': 'started'}):
                raise ValueError('Missing or invalid initialization ledger')
            await self.coordinator.recover()
            await _settled_save(self._initialization_store, {'version': 1, 'phase': 'ready'})
            self._ledger_problem = None
            self.initialization_status = 'ready'


def get_nifc_owner(hass):
    """Reuse the same owner across entries and repeated integration setup."""
    data = hass.data.setdefault(DOMAIN, {})
    if DATA_KEY not in data:
        data[DATA_KEY] = NifcOwner(async_get_clientsession(hass),
            GuardedStore(Store(hass, 1, STORE_KEY), hass.async_create_background_task),
            GuardedStore(Store(hass, 1, INITIALIZATION_KEY), hass.async_create_background_task))
    return data[DATA_KEY]
