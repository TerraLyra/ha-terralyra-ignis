"""Single-owner local research state. Corrupt storage fails closed."""
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from retry import RefreshState

LIMIT = 8_000_000


def stamp(value):
    if value is None:
        return None
    result = datetime.fromisoformat(value)
    if result.utcoffset() is None:
        raise ValueError('Naive persisted clock')
    return result


def load(path):
    try:
        with Path(path).open('rb') as handle:
            raw = handle.read(LIMIT + 1)
    except FileNotFoundError:
        return RefreshState()
    try:
        if len(raw) > LIMIT:
            raise ValueError('Storage too large')
        data = json.loads(raw)
        if type(data['version']) is not int or data['version'] != 1:
            raise ValueError('Unknown storage version')
        body = data['state']
        if type(body['failures']) is not int or body['failures'] < 0:
            raise ValueError('Invalid failure count')
        if type(body['review_required']) is not bool:
            raise ValueError('Invalid review flag')
        if body['status'] not in {'initializing','available','unavailable','rate_limited','invalid_response','review_required'}:
            raise ValueError('Invalid status')
        result = RefreshState(**body)
        result.next_attempt = stamp(body['next_attempt'])
        result.last_success_at = stamp(body['last_success_at'])
        if result.status != 'initializing' and result.next_attempt is None:
            raise ValueError('Missing cooldown')
        cached = body['last_success']
        if cached is not None:
            from fetch import decode_response
            result.last_success = decode_response(json.dumps(cached[0]).encode())
            if result.last_success_at is None:
                raise ValueError('Missing receipt timestamp')
        if result.status == 'review_required':
            result.review_required = True
        return result
    except (ValueError, TypeError, KeyError, IndexError, AttributeError):
        return RefreshState(status='storage_error', review_required=True)


def save(path, state):
    path = Path(path)
    if state.status == 'storage_error':
        raise ValueError('Do not overwrite unreadable storage')
    body = dict(vars(state))
    for key in ('next_attempt','last_success_at'):
        body[key] = body[key].isoformat() if body[key] is not None else None
    raw = json.dumps({'version':1,'state':body},allow_nan=False).encode()
    if len(raw) > LIMIT:
        raise ValueError('Storage too large')
    fd, temporary = tempfile.mkstemp(prefix=path.name+'.',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary,path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def refresh_persisted(path, fetcher, now):
    """Reserve before network I/O so a crash cannot erase the retry pause."""
    from datetime import timedelta
    state = load(path)
    if state.review_required or (state.next_attempt and now < state.next_attempt):
        return state
    reservation = RefreshState(**vars(state))
    reservation.next_attempt = now + timedelta(hours=1)
    save(path, reservation)  # Failure prevents any request.
    state.refresh(fetcher, now)
    save(path, state)
    return state
