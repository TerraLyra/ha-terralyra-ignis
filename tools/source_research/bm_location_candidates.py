"""Offline settlement mentions for review, never incident coordinates.

Callers supply a reviewed gazetteer with explicit inflected aliases. This module
has no network, geocoding, HA, persistence or production provider dependencies.
"""
from dataclasses import dataclass
import re


@dataclass(frozen=True)
class Settlement:
    identifier: str
    name: str
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class ContextHint:
    kind: str
    start: int
    end: int
    evidence: str


# Narrow lexical clues only. Unknown context is never promoted to event location.
_COUNTY = re.compile(r"(?<!\w)\w+(?:[-–]\w+)*\s+(?:vár)?megy(?:e(?:i)?|ében|éből|ének)(?!\w)", re.IGNORECASE)
_RESPONDER = re.compile(r"\s+(?:(?:hivatásos|önkéntes|önkormányzati)\s+)?(?:tűzoltók|tűzoltóság|egységek)(?!\w)", re.IGNORECASE)


def _context(value: str, start: int, end: int) -> tuple[ContextHint, ...]:
    hints = []
    for county in _COUNTY.finditer(value):
        if county.start() <= start and end <= county.end():
            hints.append(ContextHint('county_name', county.start(), county.end(), county.group()))
    responder = _RESPONDER.match(value, end)
    if value[start:end].casefold().endswith('i') and responder:
        hints.append(ContextHint('responder_reference', start, responder.end(), value[start:responder.end()]))
    return tuple(hints)


@dataclass(frozen=True)
class Mention:
    settlement_id: str
    settlement_name: str
    field: str
    start: int
    end: int
    evidence: str
    context_hints: tuple[ContextHint, ...] = ()


@dataclass(frozen=True)
class LocationReview:
    title: str
    description: str
    source_url: str
    status: str
    mentions: tuple[Mention, ...]
    multiple_candidates: bool
    input_truncated: bool
    incident_location_verified: bool = False


def review_locations(title: str, description: str, source_url: str,
                     settlements: tuple[Settlement, ...], *,
                     input_truncated: bool = False) -> LocationReview:
    """Match only explicit word-bounded aliases; preserve exact original offsets.

    Even a single mention requires review: it may identify a responding unit,
    street name, earlier incident or a negated location. No mention is promoted
    to an event location. No accent folding or suffix guessing is performed.
    Truncated input is retained but never used for candidate extraction.
    """
    if any(not isinstance(v, str) for v in (title, description, source_url)):
        raise ValueError('Report fields must be strings')
    if len(title) > 2000 or len(description) > 4000 or len(settlements) > 5000:
        raise ValueError('Review input exceeds bounds')
    seen = set()
    prepared = []
    for place in settlements:
        if not place.identifier or place.identifier in seen or not place.name.strip():
            raise ValueError('Settlements require unique IDs and nonblank names')
        seen.add(place.identifier)
        aliases = (place.name,) + place.aliases
        if len(aliases) > 32 or any(not a.strip() or len(a) > 160 for a in aliases):
            raise ValueError('Invalid settlement aliases')
        prepared.append((place, sorted(set(aliases), key=lambda a: (-len(a), a))))
    mentions = []
    if not input_truncated:
        for field, value in (('title', title), ('description', description)):
            for place, aliases in prepared:
                pattern = re.compile(r'(?<!\w)(?:' + '|'.join(map(re.escape, aliases)) + r')(?!\w)', re.IGNORECASE)
                for match in pattern.finditer(value):
                    mentions.append(Mention(place.identifier, place.name, field,
                                            match.start(), match.end(), match.group(),
                                            _context(value, match.start(), match.end())))
    mentions.sort(key=lambda m: (m.field, m.start, m.end, m.settlement_id))
    return LocationReview(title, description, source_url,
                          'requires_review' if mentions else 'unknown', tuple(mentions),
                          len({m.settlement_id for m in mentions}) > 1, input_truncated)
