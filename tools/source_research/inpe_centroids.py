"""Compatibility alias for the packaged INPE centroids module."""
import sys
from inpe_package import load
sys.modules[__name__] = load("centroids")
