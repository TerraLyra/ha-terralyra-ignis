"""Explicit INPE opt-in and bounded state selection."""
from .centroids import STATES
ENABLED = 'inpe_enabled'
SELECTED_STATES = 'inpe_states'


def settings(options):
    enabled = options.get(ENABLED, False)
    states = options.get(SELECTED_STATES, [])
    if type(enabled) is not bool or not isinstance(states, list):
        raise ValueError('Invalid INPE settings')
    if (len(states) > 3 or any(not isinstance(s, str) or s not in STATES for s in states)
            or len(set(states)) != len(states) or (enabled and not states)):
        raise ValueError('Select one to three Brazilian states')
    return enabled, tuple(sorted(states))
