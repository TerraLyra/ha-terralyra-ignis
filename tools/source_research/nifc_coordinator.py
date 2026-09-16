"""Compatibility exports for the integration-owned NIFC implementation."""
from nifc_package import load_module
_implementation = load_module("coordinator")
ResearchCoordinator = _implementation.NifcCoordinator
checkpoint = _implementation.checkpoint
restore_checkpoint = _implementation.restore_checkpoint
