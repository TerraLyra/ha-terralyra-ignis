"""Experimental ACT provider interpretation, not verified source semantics.

Never imported by production HA. Ambiguous/nonexistent civil times stay unresolved.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo
from act_times import SourceTime

PROVIDER_STATUS = 'experimental'
ENABLED_BY_DEFAULT = False

@dataclass(frozen=True)
class Interpretation:
    source: SourceTime
    status: str
    instant: Optional[datetime] = None
    rule: str = 'ACT jurisdiction Australia/Sydney; unverified provider semantics'


def interpret(source: SourceTime) -> Interpretation:
    """Apply an explicit research-only provider rule; never use machine timezone."""
    wall = source.wall_time
    if source.status != 'timezone_unverified' or wall is None:
        return Interpretation(source, source.status)
    if wall.tzinfo is not None:
        raise ValueError('Expected a naive source wall clock')
    zone = ZoneInfo('Australia/Sydney')
    candidates = {}
    for fold in (0, 1):
        local = wall.replace(tzinfo=zone, fold=fold)
        try:
            utc = local.astimezone(timezone.utc)
            if utc.astimezone(zone).replace(tzinfo=None) == wall:
                candidates[utc] = local
        except (OverflowError, ValueError):
            return Interpretation(source, 'out_of_range')
    if not candidates:
        return Interpretation(source, 'nonexistent_local_time')
    if source.zone_label:
        candidates = {utc: local for utc, local in candidates.items()
                      if local.tzname() == source.zone_label}
        if not candidates:
            return Interpretation(source, 'zone_label_conflict')
    if len(candidates) != 1:
        return Interpretation(source, 'ambiguous_local_time')
    return Interpretation(source, 'provider_interpretation_unverified', next(iter(candidates)))


def inspect_explicit_offset(raw: str) -> Interpretation:
    """Inspect CAP ISO timestamp representation without inferring event meaning."""
    import re
    source = SourceTime((raw,), 'invalid')
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-](?:[01]\d|2[0-3]):[0-5]\d)', raw):
        return Interpretation(source, 'invalid_or_missing_offset', rule='explicit source offset only')
    try:
        instant = datetime.fromisoformat(raw.replace('Z', '+00:00')).astimezone(timezone.utc)
    except (ValueError, OverflowError):
        return Interpretation(source, 'invalid', rule='explicit source offset only')
    source = SourceTime((raw,), 'explicit_offset')
    return Interpretation(source, 'explicit_offset_semantics_unverified', instant,
                          'explicit source offset only; not a revision/ignition assertion')
