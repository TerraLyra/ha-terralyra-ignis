"""Compatibility entry point for the integration-owned Canada module."""
import sys
from canada_package import load_module

_module = load_module('identity')
if __name__ == "__main__":
    import runpy
    runpy.run_module(_module.__name__, run_name="__main__")
else:
    sys.modules[__name__] = _module
