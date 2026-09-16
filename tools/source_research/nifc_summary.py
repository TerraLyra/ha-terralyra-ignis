"""Compatibility exports for the integration-owned NIFC implementation."""
from nifc_package import load_module
_implementation = load_module("summary")
summarize = _implementation.summarize
CATEGORIES = _implementation.CATEGORIES
AGES = _implementation.AGES
ROLES = _implementation.ROLES
