"""Compatibility import for offline tests of the packaged TasALERT module."""
from tasalert_package import load
_module = load("engine_storage")
globals().update({key: value for key, value in vars(_module).items() if not key.startswith("__")})
