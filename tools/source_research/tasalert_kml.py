"""Compatibility import for offline tests of the packaged TasALERT module."""
from tasalert_package import load
_module = load("kml")
globals().update({key: value for key, value in vars(_module).items() if not key.startswith("__")})
