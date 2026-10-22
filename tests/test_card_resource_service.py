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

@pytest.mark.parametrize('card,filename', [
    ('summary', 'ignis-location-summary.js'),
    ('map', 'ignis-report-map.js'),
    ('bm', 'ignis-bm-reports.js'),
])
async def test_fresh_setup_survives_collection_reload(hass, hass_storage, card, filename):
    """A first registration survives storage reload without duplicating resources."""
    from datetime import timedelta
    from homeassistant.util import dt as dt_util
    from pytest_homeassistant_custom_component.common import async_fire_time_changed

    config = SimpleNamespace(async_load=AsyncMock(return_value={}))
    collection = ResourceStorageCollection(hass, config)
    data = SimpleNamespace(resources=collection, resource_mode='storage')
    hass.data[LOVELACE_DATA] = data
    register_card_resource_service(hass)

    async def call(confirm=False):
        return await hass.services.async_call(
            'terralyra_ignis', 'register_dashboard_card',
            {'card': card, 'confirm_no_renamed_copy': confirm},
            blocking=True, return_response=True, context=Context(user_id='admin'))

    with patch.object(hass.auth, 'async_get_user', AsyncMock(
        return_value=SimpleNamespace(is_admin=True)
    )):
        preview = await call()
        assert preview['status'] == 'confirm_no_renamed_copy'
        assert preview['changed'] is False
        assert collection.async_items() == []
        assert (await call(True))['status'] == 'registered'
        original = list(collection.async_items())
        async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=15))
        await hass.async_block_till_done()

        data.resources = ResourceStorageCollection(hass, config)
        result = await call(True)
        assert result['status'] == 'already_registered'
        assert result['changed'] is False
        assert data.resources.async_items() == original
        assert original[0]['url'] == f'/terralyra_ignis/cards/{filename}'
        assert original[0]['type'] == 'module'

@pytest.mark.parametrize('inventory,expected', [
    (None, 'card_resources_unavailable'),
    ([{'url': 42, 'type': 'module'}], 'card_resources_review'),
])
async def test_setup_errors_are_translatable_and_never_write(hass, inventory, expected):
    from homeassistant.exceptions import ServiceValidationError
    collection = Mock(spec=ResourceStorageCollection)
    collection.async_get_info = AsyncMock()
    collection.async_items.return_value = inventory
    collection.async_create_item = AsyncMock()
    if inventory is not None:
        hass.data[LOVELACE_DATA] = SimpleNamespace(resources=collection, resource_mode='storage')
    register_card_resource_service(hass)
    with patch.object(hass.auth, 'async_get_user', AsyncMock(return_value=SimpleNamespace(is_admin=True))):
        with pytest.raises(ServiceValidationError) as error:
            await hass.services.async_call(
                'terralyra_ignis', 'register_dashboard_card',
                {'card': 'summary', 'confirm_no_renamed_copy': True},
                blocking=True, return_response=True, context=Context(user_id='admin'))
    assert error.value.translation_domain == 'terralyra_ignis'
    assert error.value.translation_key == expected
    collection.async_create_item.assert_not_awaited()

async def test_refresh_existing_keeps_id_and_is_idempotent(hass, hass_storage):
    """A stale query becomes a content version without duplicating the module."""
    collection = ResourceStorageCollection(hass, Mock())
    collection.loaded = True
    old = await collection.async_create_item({
        'url': '/terralyra_ignis/cards/ignis-report-map.js?v=old',
        'res_type': 'module',
    })
    hass.data[LOVELACE_DATA] = SimpleNamespace(resources=collection, resource_mode='storage')
    register_card_resource_service(hass)
    async def call():
        return await hass.services.async_call(
            'terralyra_ignis', 'register_dashboard_card',
            {'card': 'map', 'refresh_existing': True}, blocking=True,
            return_response=True, context=Context(user_id='admin'))
    with patch.object(hass.auth, 'async_get_user', AsyncMock(return_value=SimpleNamespace(is_admin=True))):
        result = await call()
        assert result['status'] == 'refreshed'
        assert result['changed'] is True
        items = collection.async_items()
        assert len(items) == 1
        assert items[0]['id'] == old['id']
        assert items[0]['type'] == 'module'
        assert items[0]['url'] == result['url']
        assert result['url'] != old['url']
        assert (await call())['changed'] is False

@pytest.mark.parametrize('inventory,mode', [
    ([], 'storage'),
    ([{'id':'a','url':'/local/ignis-report-map.js','type':'module'}], 'storage'),
    ([{'id':'a','url':'/terralyra_ignis/cards/ignis-report-map.js','type':'js'}], 'storage'),
    ([{'id':'a','url':'/terralyra_ignis/cards/ignis-report-map.js','type':'module'},
      {'id':'b','url':'/terralyra_ignis/cards/ignis-report-map.js?v=old','type':'module'}], 'storage'),
    ([{'id':'a','url':'/terralyra_ignis/cards/ignis-report-map.js','type':'module'}], 'yaml'),
])
async def test_refresh_never_adds_or_changes_ambiguous_resources(hass, inventory, mode):
    collection = Mock(spec=ResourceStorageCollection)
    collection.async_get_info = AsyncMock()
    collection.async_items.return_value = inventory
    collection.async_create_item = AsyncMock()
    collection.async_update_item = AsyncMock()
    hass.data[LOVELACE_DATA] = SimpleNamespace(resources=collection, resource_mode=mode)
    register_card_resource_service(hass)
    with patch.object(hass.auth, 'async_get_user', AsyncMock(return_value=SimpleNamespace(is_admin=True))):
        result = await hass.services.async_call(
            'terralyra_ignis', 'register_dashboard_card',
            {'card':'map', 'refresh_existing':True, 'confirm_no_renamed_copy':True},
            blocking=True, return_response=True, context=Context(user_id='admin'))
    assert result['changed'] is False
    collection.async_create_item.assert_not_awaited()
    collection.async_update_item.assert_not_awaited()
