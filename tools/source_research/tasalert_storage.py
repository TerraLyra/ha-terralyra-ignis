"""Versioned offline response-state storage. No production HA storage access."""
import base64
from dataclasses import asdict
from datetime import datetime
import json
import os
from pathlib import Path
import tempfile
from tasalert_kml import MAX_BYTES, parse_kml
from tasalert_policy import State

LIMIT = MAX_BYTES * 2
STATUSES = {'not_requested', 'retrieval_failed', 'not_modified', 'unexpected_304',
            'empty_snapshot_review', 'replacement_review', 'invalid_snapshot', 'accepted'}


def decode(raw):
    if len(raw) > LIMIT:
        raise ValueError('State exceeds limit')
    data = json.loads(raw)
    if not isinstance(data, dict) or data.pop('version', None) != 1:
        raise ValueError('Unsupported state version')
    if set(data) != {'snapshot','etag','failures','next_attempt','status'}:
        raise ValueError('Unexpected state fields')
    if type(data['failures']) is not int or not 0 <= data['failures'] <= 1000000:
        raise ValueError('Invalid failure counter')
    if data['status'] not in STATUSES:
        raise ValueError('Unknown state status')
    if data['snapshot'] is not None:
        if not isinstance(data['snapshot'],str):raise ValueError('Invalid snapshot')
        data['snapshot'] = base64.b64decode(data['snapshot'], validate=True)
        if not parse_kml(data['snapshot']):raise ValueError('Accepted snapshot cannot be empty')
    etag=data['etag']
    if etag is not None and (not isinstance(etag,str) or len(etag)>512 or any(ord(c)<32 or ord(c)==127 for c in etag)):
        raise ValueError('Invalid validator')
    if data['snapshot'] is None and etag is not None:raise ValueError('Validator without snapshot')
    if data['next_attempt'] is not None:
        data['next_attempt']=datetime.fromisoformat(data['next_attempt'])
        if data['next_attempt'].utcoffset() is None:raise ValueError('Naive deadline')
    return State(**data)


def encode(state):
    data=asdict(state)
    data['snapshot']=base64.b64encode(state.snapshot).decode('ascii') if state.snapshot is not None else None
    data['next_attempt']=state.next_attempt.isoformat() if state.next_attempt else None
    raw=json.dumps({'version':1,**data},sort_keys=True).encode()
    decode(raw)  # Validate before replacing a previously valid file.
    return raw


def save(path, state):
    atomic_write(path, encode(state))


def atomic_write(path, raw):
    path=Path(path)
    temporary=None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=path.name+'.', delete=False) as stream:
            temporary=stream.name
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary,path)
    finally:
        if temporary and os.path.exists(temporary):os.unlink(temporary)


def load(path):
    # Missing or corrupt files raise; never silently reset rate limits/history.
    with open(path,'rb') as stream:
        return decode(stream.read(LIMIT+1))
