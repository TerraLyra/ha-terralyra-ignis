"""Compatibility alias for the packaged INPE detail module."""
import sys
from inpe_package import load
sys.modules[__name__] = load("detail")
