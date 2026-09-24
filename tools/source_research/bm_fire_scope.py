"""Load the shared pure classifier without importing the HA integration package."""
from pathlib import Path
import runpy

review_fire_scope = runpy.run_path(str(
    Path(__file__).resolve().parents[2] / 'custom_components/terralyra_ignis/bm_fire_scope.py'
))['review_fire_scope']
