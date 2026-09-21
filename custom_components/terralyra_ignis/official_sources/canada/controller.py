"""Single-owner experimental controller. No scheduler or HA entities."""
import asyncio
from datetime import UTC, datetime, timedelta
from urllib.error import HTTPError
import aiohttp
from .async_transport import fetch_async
from .retry import RefreshState
from .storage import load, save


class Controller:
    def __init__(self, path, session, *, clock=lambda: datetime.now(UTC), fetcher=fetch_async):
        self.path, self.session = path, session
        self.clock, self.fetcher = clock, fetcher
        self.lock = asyncio.Lock()

    async def refresh(self):
        async with self.lock:
            state = await asyncio.to_thread(load, self.path)
            started = self.clock()
            if started.utcoffset() is None:
                raise ValueError('Aware clock required')
            if state.review_required or (state.next_attempt and started < state.next_attempt):
                return state
            reserve = RefreshState(**vars(state))
            reserve.next_attempt = started + timedelta(hours=1)
            # Finish disk operation before allowing cancellation to release ownership.
            await self._save(reserve)
            error = None
            try:
                result = await self.fetcher(self.session)
            except aiohttp.ClientResponseError as exc:
                error = HTTPError('', exc.status, 'source HTTP error', exc.headers, None)
            except (aiohttp.ClientError, OSError, TimeoutError) as exc:
                error = OSError(type(exc).__name__)
            except ValueError as exc:
                error = exc
            # CancelledError deliberately propagates; the reservation remains.
            finished = self.clock()
            if finished.utcoffset() is None:
                raise ValueError('Aware clock required')
            finished = max(started, finished)
            def outcome():
                if error is not None:
                    raise error
                return result
            state.refresh(outcome, finished)
            await self._save(state)
            return state

    async def _save(self, state):
        task = asyncio.create_task(asyncio.to_thread(save, self.path, state))
        try:
            await asyncio.shield(task)
        except asyncio.CancelledError:
            await task
            raise
