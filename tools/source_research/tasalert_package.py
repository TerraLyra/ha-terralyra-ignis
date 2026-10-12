"""Load the packaged pure modules without initializing Home Assistant."""
import importlib
from pathlib import Path
import sys
import types


def load(name):
    package_name = '_ignis_tasalert_offline'
    if package_name not in sys.modules:
        package = types.ModuleType(package_name)
        package.__path__ = [str(Path(__file__).resolve().parents[2] / 'custom_components/terralyra_ignis/official_sources/tasalert')]
        sys.modules[package_name] = package
    return importlib.import_module(package_name + '.' + name)
