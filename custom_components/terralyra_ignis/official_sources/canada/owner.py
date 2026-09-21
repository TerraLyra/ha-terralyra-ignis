"""Lazy Canada owner; not registered by integration setup yet."""
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import Store

from ...const import DOMAIN
from .controller import Controller
from .ha_storage import CanadaStore

STORE_KEY = f'{DOMAIN}.canada_state'
DATA_KEY = 'canada_owner'


def get_canada_owner(hass):
    """Share one controller and dedicated store across config entries."""
    data = hass.data.setdefault(DOMAIN, {})
    if DATA_KEY not in data:
        data[DATA_KEY] = Controller(None, async_get_clientsession(hass),
                                  store=CanadaStore(Store(hass, 1, STORE_KEY)))
    return data[DATA_KEY]
