"""Compatibility alias for the packaged INPE time module."""
import sys
from inpe_package import load
sys.modules[__name__] = load("time")
