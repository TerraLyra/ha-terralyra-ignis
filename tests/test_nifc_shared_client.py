"""NIFC borrows the actual HA session without taking ownership."""
import asyncio
import json
from unittest.mock import patch

from homeassistant.helpers.aiohttp_client import async_get_clientsession
import pytest

from custom_components.terralyra_ignis.official_sources.nifc.client import NifcClient
from custom_components.terralyra_ignis.official_sources.nifc.errors import SourceHTTPError


class Response:
    def __init__(self, status=200, started=None):
        self.status=status
        self.headers={'Retry-After':'3600'} if status==429 else {}
        self.content=self
        self.closed=False
        self.started=started
    async def __aenter__(self): return self
    async def __aexit__(self,*args): self.closed=True
    async def iter_chunked(self,size):
        if self.started:
            self.started.set()
            await asyncio.Future()
        yield json.dumps(dict(objectIdFieldName='OBJECTID',geometryType='esriGeometryPoint',
                              spatialReference={'wkid':4326},features=[],exceededTransferLimit=False)).encode()


@pytest.mark.parametrize('status',[200,429])
async def test_shared_session_survives_result_and_failure(hass,status):
    session=async_get_clientsession(hass)
    response=Response(status)
    with patch.object(session,'get',return_value=response) as get:
        if status==200:
            result=await NifcClient(session).async_fetch()
            assert result.outcome=='terminal_reported'
        else:
            with pytest.raises(SourceHTTPError) as caught:
                await NifcClient(session).async_fetch()
            assert caught.value.retry_after=='3600'
        assert get.call_args.kwargs['auto_decompress'] is False
        assert get.call_args.kwargs['allow_redirects'] is False
    assert response.closed
    assert not session.closed
    assert async_get_clientsession(hass) is session


async def test_cancellation_closes_response_but_not_shared_session(hass):
    session=async_get_clientsession(hass)
    started=asyncio.Event(); response=Response(started=started)
    with patch.object(session,'get',return_value=response):
        task=asyncio.create_task(NifcClient(session).async_fetch())
        await started.wait(); task.cancel()
        with pytest.raises(asyncio.CancelledError): await task
    assert response.closed
    assert not session.closed


async def test_inventory_transport_uses_shared_session_and_verifies_empty_result(hass):
    from unittest.mock import patch
    from homeassistant.helpers.aiohttp_client import async_get_clientsession
    from custom_components.terralyra_ignis.official_sources.nifc.client import NifcClient
    session=async_get_clientsession(hass)
    calls=[]
    async def read(borrowed,url,limit,timeout):
        assert borrowed is session
        calls.append(url)
        return b'{"objectIdFieldName":"OBJECTID","objectIds":[]}'
    with patch('custom_components.terralyra_ignis.official_sources.nifc.client._read',read):
        result=await NifcClient(session).async_fetch(inventory=True)
    assert len(calls)==2
    assert result.retrieval_method=='verified_id_inventory'
    assert not session.closed
