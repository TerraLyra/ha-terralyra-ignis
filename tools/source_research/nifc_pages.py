"""Compatibility entry point for the single integration-owned implementation."""
from nifc_package import load_module

_implementation = load_module("pages")
PageSequence = _implementation.PageSequence
inspect_pages = _implementation.inspect_pages
