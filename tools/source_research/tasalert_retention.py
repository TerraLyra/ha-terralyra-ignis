"""Offline, bounded retained-record model. No persistence or fire lifecycle claims."""
from copy import deepcopy
from datetime import datetime, timedelta
from tasalert_kml import parse_kml

RETENTION = timedelta(days=7)  # Local research policy; not a fire lifetime.
MAX_RECORDS = 5000


def reconcile(previous, raw, now, retention=RETENTION):
    """Return a new ledger; invalid input leaves caller state untouched.

    Missing records expire only after a validated snapshot and the local retention
    window. Expiry is local storage cleanup, never an upstream extinction signal.
    Existing IDs with conflicting identity/clock evidence retain their old payload.
    """
    if now.utcoffset() is None or retention <= timedelta(0):
        raise ValueError('Aware time and positive retention required')
    incoming = parse_kml(raw)
    # Empty feeds remain a review condition: do not age/delete on this evidence.
    if not incoming:
        return {'records': deepcopy(previous), 'review': ['empty_snapshot'], 'expired': []}
    if len(previous) > MAX_RECORDS:
        raise ValueError('Prior ledger exceeds capacity')
    records = deepcopy(previous)
    for entry in records.values():
        if now < entry['last_seen']:
            raise ValueError('Receipt clock regressed')
    seen, review, expired = set(), [], []
    for candidate in incoming:
        identifier=candidate['id']; seen.add(identifier)
        old=records.get(identifier)
        if old:
            a,b=old['record'],candidate
            conflict=any(a['fields'].get(k)!=b['fields'].get(k) for k in ('feedType','number'))
            for clock in ('created','changed'):
                av,bv=a['record_times'].get(clock),b['record_times'].get(clock)
                if bool(av)!=bool(bv):conflict=True
                elif av:
                    ad,bd=datetime.fromisoformat(av),datetime.fromisoformat(bv)
                    if (clock=='created' and ad!=bd) or (clock=='changed' and bd<ad):conflict=True
            if a!=b:
                av,bv=a['record_times'].get('changed'),b['record_times'].get('changed')
                if not av or not bv or datetime.fromisoformat(bv)<=datetime.fromisoformat(av):conflict=True
            if conflict:
                old['presence']='review_required'
                review.append(identifier)
                continue
        records[identifier]={'record':candidate,'last_seen':now,'presence':'in_snapshot'}
    for identifier in list(records):
        if identifier in seen:continue
        entry=records[identifier]
        entry['presence']='not_in_snapshot'
        if now-entry['last_seen']>=retention:
            expired.append(identifier)
            del records[identifier]
    if len(records)>MAX_RECORDS:
        raise ValueError('Ledger capacity exceeded; previous state must be retained')
    return {'records':records,'review':review,'expired':expired}
