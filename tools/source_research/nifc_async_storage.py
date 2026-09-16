"""Compatibility exports for the integration-owned NIFC implementation."""
from nifc_package import load_module
_implementation = load_module("stored_coordinator")
AsyncStoredResearchCoordinator = _implementation.NifcStoredCoordinator
_settled_save = _implementation._settled_save
