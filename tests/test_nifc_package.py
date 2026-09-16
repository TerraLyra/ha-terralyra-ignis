"""Production imports and standalone research wrappers use identical pure code."""
from importlib import import_module
from pathlib import Path

from custom_components.terralyra_ignis.official_sources.nifc import assessment, page, pages, records


def test_research_wrappers_share_production_identity(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / 'tools' / 'source_research'))
    for wrapper, implementation, names in (
        ('nifc_page',page,('PageInspection','inspect_page')),
        ('nifc_pages',pages,('PageSequence','inspect_pages')),
        ('nifc_records',records,('IncidentRecord','normalize_page')),
        ('nifc_assessment',assessment,('source_age','complex_roles')),
    ):
        research = import_module(wrapper)
        for name in names:
            assert getattr(research,name) is getattr(implementation,name)


def test_normalized_record_is_integration_owned(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / 'tools' / 'source_research'))
    fixture=import_module('test_nifc_records').sample()
    record, = records.normalize_page(fixture)
    assert type(record) is records.IncidentRecord
    assert record.__class__.__module__ == 'custom_components.terralyra_ignis.official_sources.nifc.records'


def test_runtime_state_and_research_wrappers_share_identity(monkeypatch):
    from custom_components.terralyra_ignis.official_sources.nifc import (
        coordinator, refresh, stored_coordinator, summary,
    )
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / 'tools' / 'source_research'))
    assert import_module('nifc_refresh').RefreshState is refresh.RefreshState
    assert import_module('nifc_coordinator').ResearchCoordinator is coordinator.NifcCoordinator
    assert import_module('nifc_async_storage').AsyncStoredResearchCoordinator is stored_coordinator.NifcStoredCoordinator
    assert import_module('nifc_summary').summarize is summary.summarize
