"""Load only the pure package for standalone tests without importing HA setup.

The canonical module name is retained so HA tests and research wrappers share class
identity. No parent package is fabricated or replaced. Production never imports this
helper: it uses ordinary relative imports within official_sources.canada.
"""
import importlib
import importlib.util
from pathlib import Path
import sys

PACKAGE = 'custom_components.terralyra_ignis.official_sources.canada'
PATH = Path(__file__).resolve().parents[3] / 'custom_components' / 'terralyra_ignis' / 'official_sources' / 'canada'


def load_module(name):
    if name not in ('geometry', 'identity', 'inspect_sample', 'records', 'fetch', 'async_transport', 'retry', 'storage', 'controller', 'presentation', 'lifecycle'):
        raise ValueError('Unknown pure Canada module')
    if PACKAGE not in sys.modules:
        spec = importlib.util.spec_from_file_location(PACKAGE, PATH / '__init__.py',
                                                     submodule_search_locations=[str(PATH)])
        if spec is None or spec.loader is None:
            raise ImportError('Canada pure package unavailable')
        module = importlib.util.module_from_spec(spec)
        sys.modules[PACKAGE] = module
        try:
            spec.loader.exec_module(module)
        except BaseException:
            sys.modules.pop(PACKAGE, None)
            raise
    return importlib.import_module(f'{PACKAGE}.{name}')
