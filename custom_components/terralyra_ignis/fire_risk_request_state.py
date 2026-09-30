"""Opt-in FRMv3 request gate with durable provider cooldown recovery."""
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import Protocol, TypeVar

from .fire_risk_requests import ForecastRequestGate
from .products.fire_risk import FireRiskError

_T = TypeVar("_T")
_PROVIDER = "eumetsat_lsa_saf_frmv3"


class CooldownStore(Protocol):
    """Subset of HA Store used here; owner supplies one installation-wide store."""

    async def async_load(self) -> object:
        """Load provider state, or None on first use."""

    async def async_save(self, data: dict) -> None:
        """Persist state before another provider request is allowed."""


class ForecastStateError(FireRiskError):
    """Local state could not be recovered/saved; no implicit network fallback."""


class PersistentForecastRequestGate(ForecastRequestGate):
    """Recover once and durably save cooldown before releasing queued peers.

    Share one instance and store across entries/locations for FRMv3.
    It never deletes storage.
    Failed writes remain dirty and must succeed before further network traffic.
    """

    def __init__(self, store: CooldownStore, **kwargs) -> None:
        super().__init__(**kwargs)
        self._store = store
        self._state_lock = asyncio.Lock()
        self._loaded = False
        self._dirty = False
        self._saved_deadline = 0.0

    async def _restore(self) -> None:
        try:
            payload = await self._store.async_load()
        except Exception as err:
            raise ForecastStateError("Forecast cooldown state could not be loaded") from err
        if payload is not None:
            try:
                if (not isinstance(payload, dict)
                        or type(payload.get("schema")) is not int
                        or payload["schema"] != 1 or payload.get("provider") != _PROVIDER
                        or "cooldown" not in payload):
                    raise ValueError("Invalid state envelope")
                cooldown = payload["cooldown"]
                if cooldown is not None and not self.import_cooldown(cooldown):
                    # An expired valid deadline is harmless; malformed/future
                    # state must not silently erase a potentially active pause.
                    if (not isinstance(cooldown, dict)
                            or type(cooldown.get("schema")) is not int
                            or cooldown["schema"] != 1
                            or not isinstance(cooldown.get("until"), str)):
                        raise ValueError("Invalid cooldown")
                    until = datetime.fromisoformat(cooldown["until"])
                    if until.tzinfo is None or until.utcoffset() is None or until > self._utcnow():
                        raise ValueError("Unsafe cooldown deadline")
            except (ValueError, TypeError, OverflowError) as err:
                raise ForecastStateError("Forecast cooldown state is invalid") from err
        self._saved_deadline = self._cooldown_until
        self._loaded = True

    async def _save(self) -> None:
        try:
            await self._store.async_save({
                "schema": 1, "provider": _PROVIDER,
                "cooldown": self.export_cooldown(),
            })
        except Exception as err:
            raise ForecastStateError("Forecast cooldown state could not be saved") from err
        self._saved_deadline = self._cooldown_until
        self._dirty = False

    async def run(self, operation: Callable[[], Awaitable[_T]]) -> _T:
        async with self._state_lock:
            if not self._loaded:
                await self._restore()
            if self._dirty:
                await self._save()
            try:
                return await super().run(operation)
            finally:
                if self._cooldown_until != self._saved_deadline:
                    self._dirty = True
                    await self._save()


def get_forecast_request_gate(hass) -> PersistentForecastRequestGate:
    """One provider-wide gate/store, shared by Home and all location clients."""
    from homeassistant.helpers.storage import Store
    from .const import DOMAIN

    owners = hass.data.setdefault(DOMAIN, {})
    if "frmv3_request_gate" not in owners:
        owners["frmv3_request_gate"] = PersistentForecastRequestGate(
            Store(hass, 1, f"{DOMAIN}.frmv3_request_cooldown"))
    return owners["frmv3_request_gate"]
