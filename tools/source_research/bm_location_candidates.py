"""Offline settlement mentions for review, never incident coordinates.

Callers supply a reviewed gazetteer with explicit inflected aliases. This module
has no network, geocoding, HA, persistence or production provider dependencies.
"""
from dataclasses import dataclass
import re


# Bounded country-level name research, including the full filtered HU extract.
MAX_SETTLEMENTS = 20000


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
_RESPONDER = re.compile(r"\s+(?:(?:hivatásos|önkéntes|önkormányzati)\s+)?(?:tűzoltók(?:at)?|tűzoltóság|egységek(?:et)?)(?!\w)", re.IGNORECASE)


# Explicit street suffix only; retain the mention and original evidence.
_STREET = re.compile(r"[ \t]+(?:utca|utcában|utcán|utcai|utcába|utcából|út|úton|úti|útra|útról|útján|tér|téren|téri|térre|térről|köz|közben)(?!\w)", re.IGNORECASE)


# Exact observed adjective/noun construction; never a global place blacklist.
_COLLISION_COUNT = re.compile(r"(?<!\w)négyes[ \t]+karambol(?!\w)", re.IGNORECASE)


# Narrow transport constructions. Unknown endpoint text can supply context for a
# known mention, but never creates a new place or an inferred coordinate.
_ROUTE_PATTERNS = (
    re.compile(r"(?<!\w)\w+(?:ról|ről|ból|ből)[ \t]+\w+(?:ba|be|ra|re)[ \t]+tartó[ \t]+(?:vonat|busz|autóbusz)(?!\w)", re.IGNORECASE),
    re.compile(r"(?<!\w)\w+[ \t]+és[ \t]+\w+[ \t]+között[ \t]+(?:pótlóbuszokkal|pótlóbuszok|pótlóbusz|vonattal|autóbusszal)(?!\w)", re.IGNORECASE),
)


def _context(value: str, start: int, end: int) -> tuple[ContextHint, ...]:
    hints = []
    for county in _COUNTY.finditer(value):
        if county.start() <= start and end <= county.end():
            hints.append(ContextHint('county_name', county.start(), county.end(), county.group()))
    for phrase in _COLLISION_COUNT.finditer(value):
        if phrase.start() == start and value[start:end].casefold() == 'négyes':
            hints.append(ContextHint('possible_vehicle_count', phrase.start(), phrase.end(), phrase.group()))
    for pattern in _ROUTE_PATTERNS:
        for route in pattern.finditer(value):
            if route.start() <= start and end <= route.end():
                hints.append(ContextHint('transport_route_reference', route.start(), route.end(), route.group()))
    street = _STREET.match(value, end)
    if street:
        hints.append(ContextHint('street_name_reference', start, street.end(), value[start:street.end()]))
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
    if len(title) > 2000 or len(description) > 4000 or len(settlements) > MAX_SETTLEMENTS:
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
    # Use only known reviewed aliases, not arbitrary adjective-like words.
    adjectives = sorted({a for _, aliases in prepared for a in aliases
                         if a.casefold().endswith('i')}, key=lambda a: (-len(a), a))
    list_pattern = None
    if adjectives:
        name = '(?:' + '|'.join(map(re.escape, adjectives)) + ')'
        # A shared final noun may follow individually qualified units:
        # 'ajkai hivatásos és a somlóvásárhelyi önkéntes tűzoltókat'.
        # Horizontal whitespace only: do not propagate across lines/sentences.
        modifier = r'(?:[ \t]+(?:hivatásos|önkéntes|önkormányzati))?'
        member = name + r'(?!\w)' + modifier
        separator = r'(?:[ \t]*,[ \t]*(?:(?:és|illetve)[ \t]+)?|[ \t]+(?:és|illetve)[ \t]+)(?:(?:a|az)[ \t]+)?'
        noun = r'[ \t]+(?:tűzoltók(?:at)?|tűzoltóság|egységek(?:et)?)(?!\w)'
        list_pattern = re.compile(r'(?<!\w)' + member + '(?:' + separator + member
                                  + r'){1,7}' + noun, re.IGNORECASE)
    mentions = []
    if not input_truncated:
        for field, value in (('title', title), ('description', description)):
            lists = list(list_pattern.finditer(value)) if list_pattern else []
            for place, aliases in prepared:
                pattern = re.compile(r'(?<!\w)(?:' + '|'.join(map(re.escape, aliases)) + r')(?!\w)', re.IGNORECASE)
                for match in pattern.finditer(value):
                    contexts = _context(value, match.start(), match.end())
                    for group in lists:
                        if group.start() <= match.start() and match.end() <= group.end():
                            contexts += (ContextHint('responder_list_reference', group.start(),
                                                     group.end(), group.group()),)
                    mentions.append(Mention(place.identifier, place.name, field,
                                            match.start(), match.end(), match.group(),
                                            contexts))
    mentions.sort(key=lambda m: (m.field, m.start, m.end, m.settlement_id))
    return LocationReview(title, description, source_url,
                          'requires_review' if mentions else 'unknown', tuple(mentions),
                          len({m.settlement_id for m in mentions}) > 1, input_truncated)
