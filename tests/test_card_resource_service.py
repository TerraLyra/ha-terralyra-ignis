"""Explicit resource registration preserves existing configuration."""
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch
import pytest
from homeassistant.core import Context
from homeassistant.exceptions import Unauthorized
from homeassistant.components.lovelace.const import LOVELACE_DATA
from homeassistant.components.lovelace.resources import ResourceStorageCollection
from custom_components.terralyra_ignis.card_resource_service import register_card_resource_service

async def test_preview_confirm_repeat_and_yaml(hass):
    items=[]
    collection=Mock(spec=ResourceStorageCollection)
    collection.async_get_info=AsyncMock()
    collection.async_items.side_effect=lambda:items
    async def create(data):
        items.append({'url':data['url'],'type':data['res_type']})
    collection.async_create_item=AsyncMock(side_effect=create)
    data=SimpleNamespace(resources=collection,resource_mode='storage')
    hass.data[LOVELACE_DATA]=data
    register_card_resource_service(hass)
    async def call(confirm=False):
        return await hass.services.async_call('terralyra_ignis','register_dashboard_card',
            {'card':'summary','confirm_no_renamed_copy':confirm},blocking=True,
            return_response=True,context=Context(user_id='admin'))
    with patch.object(hass.auth,'async_get_user',AsyncMock(return_value=SimpleNamespace(is_admin=True))):
        assert (await call())['changed'] is False
        collection.async_create_item.assert_not_awaited()
        assert (await call(True))['status']=='registered'
        assert (await call(True))['status']=='already_registered'
        collection.async_create_item.assert_awaited_once()
        data.resource_mode='yaml'
        assert (await call(True))['status']=='yaml_manual_setup'
        collection.async_create_item.assert_awaited_once()

async def test_requires_identified_administrator(hass):
    register_card_resource_service(hass)
    for user in (None,'nonadmin'):
        with patch.object(hass.auth,'async_get_user',AsyncMock(return_value=SimpleNamespace(is_admin=False))):
            with pytest.raises(Unauthorized):
                await hass.services.async_call('terralyra_ignis','register_dashboard_card',
                    {'card':'summary'},blocking=True,return_response=True,context=Context(user_id=user))

async def test_real_collection_persists_module(hass, hass_storage):
    collection=ResourceStorageCollection(hass, Mock())
    collection.loaded=True
    hass.data[LOVELACE_DATA]=SimpleNamespace(resources=collection,resource_mode='storage')
    register_card_resource_service(hass)
    with patch.object(hass.auth,'async_get_user',AsyncMock(return_value=SimpleNamespace(is_admin=True))):
        result=await hass.services.async_call('terralyra_ignis','register_dashboard_card',
            {'card':'map','confirm_no_renamed_copy':True},blocking=True,
            return_response=True,context=Context(user_id='admin'))
    assert result['changed'] is True
    assert len(collection.async_items())==1
    assert collection.async_items()[0]['type']=='module'
    assert collection.async_items()[0]['url'].endswith('/ignis-report-map.js')
