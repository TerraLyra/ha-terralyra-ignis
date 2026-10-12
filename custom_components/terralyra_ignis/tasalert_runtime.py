"""One opt-in TasALERT retrieval owner across all entries; inert by default."""
import asyncio
from datetime import timedelta
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import callback
from homeassistant.helpers.event import async_track_time_interval
from .const import DOMAIN
from .monitoring import resolve_monitored_locations
from .official_sources.tasalert.owner import create_owner


class TasAlertRuntime:
    def __init__(self,hass,owner):
        self.hass,self.owner=hass,owner
        self.listeners={}
        self.timer=None
        self.task=None
        self.stopping=False
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP,self.async_stop)

    @property
    def enabled(self):
        return not self.stopping and any(any(loc.enabled for loc in resolve_monitored_locations(self.hass,entry)) for entry,_ in self.listeners.values())

    @callback
    def attach(self,entry,listener,*,consumer="diagnostic"):
        self.listeners[(entry.entry_id,consumer)]=(entry,listener)
        if self.timer is None and not self.stopping:
            self.timer=async_track_time_interval(self.hass,self.request_refresh,timedelta(minutes=1))
        self.request_refresh()

    @callback
    def notify(self):
        for _,listener in tuple(self.listeners.values()):listener()

    @callback
    def request_refresh(self,_now=None):
        if not self.enabled or self.owner.blocked or self.owner.initialization_required:return
        if self.task is None or self.task.done():
            self.task=self.hass.async_create_background_task(self._run(),'TasALERT refresh')
            self.task.add_done_callback(self._finished)

    def _finished(self,task):
        if not task.cancelled():task.exception()
        self.notify()

    async def _run(self):
        try:
            if self.owner.state is None:await self.owner.async_load()
            if self.enabled:await self.owner.async_refresh()
        except (OSError,ValueError):pass

    async def detach(self,entry,*,consumer="diagnostic"):
        self.listeners.pop((entry.entry_id,consumer),None)
        if not self.listeners:
            if self.timer:self.timer();self.timer=None
            if self.task and not self.task.done():
                self.task.cancel()
                await asyncio.gather(self.task,return_exceptions=True)

    async def async_stop(self,_event=None):
        self.stopping=True
        if self.timer:self.timer();self.timer=None
        if self.task and not self.task.done():
            self.task.cancel()
            await asyncio.gather(self.task,return_exceptions=True)
        await self.owner.async_close()


def get_tasalert_runtime(hass):
    data=hass.data.setdefault(DOMAIN,{})
    if 'tasalert_runtime' not in data:data['tasalert_runtime']=TasAlertRuntime(hass,create_owner(hass))
    return data['tasalert_runtime']
