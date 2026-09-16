"""Compatibility entry point for the single integration-owned implementation."""
from nifc_package import load_module

_implementation = load_module("assessment")
source_age = _implementation.source_age
complex_roles = _implementation.complex_roles
