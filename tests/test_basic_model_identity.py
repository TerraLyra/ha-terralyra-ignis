"""The HA compatibility import must not create duplicate model classes."""
from custom_components.terralyra_ignis import basic_models, models


def test_legacy_model_imports_preserve_class_identity():
    for name in ("FireDetection", "ProviderSnapshot", "ProviderStatus"):
        assert getattr(models, name) is getattr(basic_models, name)


def test_bundled_models_satisfy_standalone_consumer_contract(monkeypatch):
    from importlib import import_module
    from pathlib import Path
    import unittest

    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "tools"))
    suite = import_module("model_consumer_contract").consumer_suite(models)
    result = unittest.TestResult()
    suite.run(result)
    assert result.testsRun == 3
    assert result.wasSuccessful(), (result.failures, result.errors)
