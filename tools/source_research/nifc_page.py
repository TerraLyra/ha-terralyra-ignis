"""Compatibility entry point for the single integration-owned implementation."""
from nifc_package import load_module

_implementation = load_module("page")
PageInspection = _implementation.PageInspection
inspect_page = _implementation.inspect_page
