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
