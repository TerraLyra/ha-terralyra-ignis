"""Compatibility exports for the integration-owned NIFC implementation."""
from nifc_package import load_module
_implementation = load_module("refresh")
RefreshState = _implementation.RefreshState
SourceHTTPError = _implementation.SourceHTTPError
retry_after_seconds = _implementation.retry_after_seconds
due = _implementation.due
failed = _implementation.failed
succeeded = _implementation.succeeded
_clock = _implementation._clock
