"""NIFC repair diagnostics use real HA issue registry, without source activation."""
import json
from pathlib import Path
from types import SimpleNamespace

from homeassistant.helpers import issue_registry as ir
import pytest

from custom_components.terralyra_ignis.repairs import async_sync_nifc_research_issue

DOMAIN = 'terralyra_ignis'


@pytest.mark.parametrize('problem,key', [
    ('storage_load_failed','nifc_storage_load'),
    ('storage_save_failed','nifc_storage_save'),
    ('review_required','nifc_review_required'),
    ('request_failed','nifc_review_required'),
    ('refresh_failed_invalid_data','nifc_source_invalid'),
    ('refresh_failed_access_denied','nifc_access_denied'),
])
async def test_actionable_issue_translated_and_not_auto_fixable(hass,problem,key):
    async_sync_nifc_research_issue(hass,SimpleNamespace(entry_id='test'),enabled=True,problem=problem)
    issue=ir.async_get(hass).async_get_issue(DOMAIN,'test_nifc_research')
    assert issue.translation_key == key
    assert issue.is_fixable is False
    assert issue.severity is ir.IssueSeverity.WARNING
    assert not issue.translation_placeholders
    root=Path(__file__).resolve().parents[1]/'custom_components'/DOMAIN
    for filename in ('strings.json','translations/en.json','translations/hu.json'):
        assert json.loads((root/filename).read_text())['issues'][key]['description']


async def test_scoped_recovery_preserves_other_entry_and_issues(hass):
    registry=ir.async_get(hass)
    for name in ('one','two'):
        async_sync_nifc_research_issue(hass,SimpleNamespace(entry_id=name),enabled=True,problem='review_required')
    async_sync_nifc_research_issue(hass,SimpleNamespace(entry_id='one'),enabled=True,problem=None)
    assert registry.async_get_issue(DOMAIN,'one_nifc_research') is None
    assert registry.async_get_issue(DOMAIN,'two_nifc_research') is not None
    async_sync_nifc_research_issue(hass,SimpleNamespace(entry_id='two'),enabled=False)
    assert registry.async_get_issue(DOMAIN,'two_nifc_research') is None


@pytest.mark.parametrize('problem',['not_loaded','refresh_failed_transient','refresh_failed_rate_limited','private/path',{}])
async def test_unknown_and_transient_status_do_not_clear_review_issue(hass,problem):
    entry=SimpleNamespace(entry_id='test')
    async_sync_nifc_research_issue(hass,entry,enabled=True,problem='review_required')
    async_sync_nifc_research_issue(hass,entry,enabled=True,problem=problem)
    issue=ir.async_get(hass).async_get_issue(DOMAIN,'test_nifc_research')
    assert issue.translation_key == 'nifc_review_required'
