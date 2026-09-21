"""HA imports and standalone Canada checks exercise the same implementation."""
from importlib import import_module
from pathlib import Path

from custom_components.terralyra_ignis.official_sources.canada import (
    controller, lifecycle, presentation, records, storage,
)


def test_research_and_ha_share_implementation(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]
                                   / 'tools' / 'source_research' / 'canada'))
    for module, symbol in ((controller, 'Controller'), (lifecycle, 'Lifecycle'),
                           (presentation, 'match_locations'), (records, 'project_record'),
                           (storage, 'load')):
        wrapper = import_module(module.__name__.rsplit('.', 1)[-1])
        assert getattr(wrapper, symbol) is getattr(module, symbol)


def test_construction_is_inert(tmp_path):
    path = tmp_path / 'canada.json'
    owner = controller.Controller(path, None)
    runtime = lifecycle.Lifecycle(owner)
    assert runtime.task is None
    assert not runtime.consumers
    assert runtime.last_state is None
    assert not path.exists()
