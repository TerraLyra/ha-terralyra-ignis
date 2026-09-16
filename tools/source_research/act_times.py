"""Offline source-time inspection; no timezone or ignition-time inference."""
from dataclasses import dataclass
from datetime import datetime
import re
from typing import Optional

from act_feed import ActItem


@dataclass(frozen=True)
class SourceTime:
    raw_values: tuple[str, ...]
    status: str
    wall_time: Optional[datetime] = None
    zone_label: str = ''


@dataclass(frozen=True)
class ActTimes:
    publication: SourceTime
    updated: SourceTime
    call: SourceTime


MONTHS = {name: i for i, name in enumerate(
    ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'), 1)}


def _parse(values, publication=False):
    if not values:
        return SourceTime((), 'missing')
    if len(values) != 1:
        return SourceTime(values, 'duplicate')
    raw = values[0].strip()
    if publication:
        match = re.fullmatch(r'([0-9]{4})-([0-9]{2})-([0-9]{2}) ([0-9]{2}):([0-9]{2}) (AEST|AEDT)', raw)
    else:
        match = re.fullmatch(r'([0-9]{1,2}) ([A-Za-z]{3}) ([0-9]{4}) ([0-9]{2}):([0-9]{2}):([0-9]{2})(?:\.([0-9]{1,6}))?', raw)
    if not match:
        return SourceTime(values, 'invalid')
    try:
        if publication:
            year, month, day, hour, minute, zone = match.groups()
            wall = datetime(*map(int, (year, month, day, hour, minute)))
        else:
            day, month, year, hour, minute, second, fraction = match.groups()
            wall = datetime(int(year), MONTHS[month], int(day), int(hour), int(minute),
                            int(second), int((fraction or '').ljust(6, '0')))
            zone = ''
    except (ValueError, KeyError):
        return SourceTime(values, 'invalid')
    # A parsed local clock reading is NOT an aware instant. Even the observed AEST
    # label needs provider summer/DST verification; do not attach HA's timezone.
    return SourceTime(values, 'timezone_unverified', wall, zone)


def inspect_times(item: ActItem) -> ActTimes:
    fields = dict(item.fields)
    if len(fields) != len(item.fields):
        raise ValueError('Duplicate raw fields')
    description = fields.get('description', '')
    def labelled(label):
        return tuple(line[len(label):].strip() for line in description.splitlines()
                     if line.startswith(label))
    publication = (fields['pubDate'],) if 'pubDate' in fields else ()
    return ActTimes(_parse(publication, True), _parse(labelled('Updated:')),
                    _parse(labelled('Time of Call:')))
