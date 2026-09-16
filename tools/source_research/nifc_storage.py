"""Explicit cooldown-only file storage for research, outside HA runtime."""
from pathlib import Path
import json
import os
import tempfile

from nifc_coordinator import checkpoint, restore_checkpoint

FILENAME = 'nifc-research-cooldown.json'
MAX_BYTES = 4096


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate checkpoint key')
        result[key] = value
    return result


def load_cooldown(directory, *, now):
    """Missing, oversized or corrupt files raise; caller must explicitly initialize.

    Use a trusted application-owned directory. Cross-process writers are unsupported.
    """
    path = Path(directory) / FILENAME
    if path.is_symlink():
        raise ValueError('Checkpoint must not be a symbolic link')
    with path.open('rb') as stream:
        payload = stream.read(MAX_BYTES + 1)
    if len(payload) > MAX_BYTES:
        raise ValueError('Oversized cooldown checkpoint')
    data = json.loads(payload.decode('utf-8'), object_pairs_hook=_pairs)
    return restore_checkpoint(data, now=now)


def save_cooldown(directory, state, *, now):
    """Validate, flush and atomically replace only the dedicated cooldown file.

    Parent directory must exist. File contents are fsynced before replacement;
    directory metadata is not fsynced, so sudden power-loss durability is not claimed.
    No history/cache files are read, scanned or removed.
    """
    directory = Path(directory)
    path = directory / FILENAME
    if path.is_symlink():
        raise ValueError('Checkpoint must not be a symbolic link')
    data = checkpoint(state, now=now)
    restore_checkpoint(data, now=0)
    payload = json.dumps(data, allow_nan=False, separators=(',', ':')).encode('utf-8')
    if len(payload) > MAX_BYTES:
        raise ValueError('Oversized cooldown checkpoint')
    fd, name = tempfile.mkstemp(prefix='.nifc-cooldown-', suffix='.tmp', dir=directory)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)
