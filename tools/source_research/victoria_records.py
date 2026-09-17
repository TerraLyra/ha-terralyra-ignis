"""Experimental Victoria identity/time evidence. No persistence or HA imports."""
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional
from zoneinfo import ZoneInfo
import re


@dataclass(frozen=True)
class TimeEvidence:
    raw_epoch: object
    raw_local: object
    status: str
    epoch_candidate: Optional[datetime] = None
    rule: str = 'unverified: epoch milliseconds and dd/mm/yyyy Australia/Melbourne'


def inspect_update(record: dict) -> TimeEvidence:
    """Compare source fields; never infer an instant from a missing epoch.

    An exact match supports the candidate representation, not update-time meaning.
    Yearless display strings are retained by the caller and never fill missing years.
    """
    epoch, raw = record.get('lastUpdatedDt'), record.get('lastUpdateDateTime')
    def result(status, instant=None):
        return TimeEvidence(epoch, raw, status, instant)
    if epoch is None:
        return result('missing_epoch')
    if type(epoch) is not int:
        return result('invalid_epoch')
    try:
        instant = datetime(1970,1,1,tzinfo=timezone.utc)+timedelta(milliseconds=epoch)
    except (OverflowError, ValueError):
        return result('invalid_epoch')
    if raw is None:
        return result('missing_local', instant)
    if not isinstance(raw,str) or not re.fullmatch(r'[0-9]{2}/[0-9]{2}/[0-9]{4} [0-9]{2}:[0-9]{2}:[0-9]{2}',raw):
        return result('invalid_local', instant)
    try:
        day,month,year,hour,minute,second=map(int,re.split(r'[/ :]',raw))
        wall=datetime(year,month,day,hour,minute,second)
        zone=ZoneInfo('Australia/Melbourne')
        valid=[]
        for fold in (0,1):
            candidate=wall.replace(tzinfo=zone,fold=fold).astimezone(timezone.utc)
            if candidate.astimezone(zone).replace(tzinfo=None)==wall and candidate not in valid:
                valid.append(candidate)
        observed=instant.astimezone(zone).replace(tzinfo=None)
    except (ValueError,OverflowError):
        return result('invalid_local',instant)
    if not valid:
        return result('nonexistent_local_time',instant)
    # Local source text has second precision; retain epoch milliseconds separately.
    if observed.replace(microsecond=0)!=wall:
        return result('conflict',instant)
    return result('fold_match_unverified' if len(valid)>1 else 'match_unverified',instant)


def inspect_id(record: dict):
    """Preserve type and exact value; never coerce/trim/merge source identifiers."""
    value=record.get('incidentNo')
    if value is None:
        return 'missing',None
    if type(value) is int and value>0:
        return 'candidate',('integer',value)
    if isinstance(value,str) and value and value==value.strip() and not any(ord(c)<32 for c in value):
        return 'candidate',('string',value)
    return 'invalid',None


def summarize_records(records):
    """Fixed counts only, including duplicates; no winner selection or raw IDs."""
    identity=Counter(); times=Counter(); ids=Counter()
    for record in records:
        status,key=inspect_id(record)
        identity[status]+=1
        if key is not None:ids[key]+=1
        times[inspect_update(record).status]+=1
    return {'status':'experimental','production_readiness':'not_established',
            'record_count':len(records),'identity':dict(sorted(identity.items())),
            'update_times':dict(sorted(times.items())),
            'duplicate_id_groups':sum(count>1 for count in ids.values())}


def compare_ids(before,after):
    """Two snapshots show overlap only, never lifetime stability or fire closure."""
    def keys(records):
        found=[]
        for record in records:
            status,key=inspect_id(record)
            if status!='candidate':raise ValueError('Unusable identity in snapshot')
            found.append(key)
        if len(found)!=len(set(found)):raise ValueError('Duplicate identity in snapshot')
        return set(found)
    old,new=keys(before),keys(after)
    return {'shared':len(old & new),'only_before':len(old-new),'only_after':len(new-old),
            'identity_stability':'not_established'}
