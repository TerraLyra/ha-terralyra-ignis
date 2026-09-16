"""Compatibility entry point for the single integration-owned implementation."""
from nifc_package import load_module

_implementation = load_module("records")
IncidentRecord = _implementation.IncidentRecord
normalize_page = _implementation.normalize_page
