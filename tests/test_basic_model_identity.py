"""The HA compatibility import must not create duplicate model classes."""
from custom_components.terralyra_ignis import basic_models, models


def test_legacy_model_imports_preserve_class_identity():
    for name in ("FireDetection", "ProviderSnapshot", "ProviderStatus"):
        assert getattr(models, name) is getattr(basic_models, name)
