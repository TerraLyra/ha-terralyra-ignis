"""Small satellite-first BM text matcher; no NLP model or event creation.

Match only explicitly locative forms of a supplied settlement, in the same
clause as an affirmative fire statement. Missing evidence means no annotation.
"""
from __future__ import annotations

import re
from datetime import datetime

from .bm_satellite_context import BMTownReport

_FIRE = re.compile(r'\b(?:ég|égett|égnek|égtek|lángol|lángolt|kigyulladt|kigyulladtak|tűz ütött ki|tűz keletkezett|lángra kapott)\b', re.I)
_VETO = re.compile(r'\b(?:nem|nincs|téves|gyakorlat|gyakorlaton|feltételezett|megelőzés|megelőzési)\b', re.I)
_ROLE = re.compile(r'^\s*(?:felé|utca\w*|út\w*|tér\w*|köz\w*|tűzolt\w*|(?:hivatásos|önkéntes|önkormányzati|létesítményi)\s+tűzolt\w*)\b', re.I)
_SUFFIXES = ('ban', 'ben', 'on', 'en', 'ön', 'n', 'nál', 'nél')


def locative_pattern(name: str):
    """Bounded spelling variants, not a morphological analyzer.

    The uninflected name alone is never accepted. Lengthened final a/e and
    explicit nearby/edge constructions cover common Hungarian feed phrasing.
    """
    if not isinstance(name, str) or not name.strip() or len(name) > 160:
        raise ValueError('Bounded settlement name required')
    stem = name[:-1] + {'a':'á', 'e':'é'}.get(name[-1], name[-1])
    forms = {stem + suffix for suffix in _SUFFIXES}
    return re.compile(r'(?<!\w)(?:' + '|'.join(re.escape(v) for v in sorted(forms, key=len, reverse=True))
                      + '|' + re.escape(name) + r'\s+(?:közelében|határában|térségében))(?!\w)', re.I)


def lightweight_report(notice, settlement_names):
    """Build context from current RSS text and unambiguous supplied town IDs.

    settlement_names maps stable IDs to names, supplied by the satellite
    gazetteer adapter. Homonymous names are rejected. Never parse responder
    adjectives, infer coordinates, fetch articles or persist automatic reviews.
    """
    if len(settlement_names) > 500:
        raise ValueError('Too many satellite settlements')
    title, description = notice.get('title', ''), notice.get('description', '')
    if any(not isinstance(t, str) or len(t) > 6000 for t in (title, description)):
        raise ValueError('Bounded current RSS text required')
    names = {}
    for identifier, name in settlement_names.items():
        names.setdefault(name.casefold(), []).append(identifier)
    accepted, evidence = set(), []
    if notice.get('description_status') != 'truncated':
        for identifier, name in settlement_names.items():
            if len(names[name.casefold()]) != 1:
                continue
            pattern = locative_pattern(name)
            for field, text in (('title', title), ('description', description)):
                # Do not carry a fire assertion across sentences/semicolon clauses.
                for clause in re.finditer(r'[^.!?;\n]+', text):
                    value = clause.group()
                    if not _FIRE.search(value) or _VETO.search(value) or re.search(r'\btűzolt\w*\b', value, re.I):
                        continue
                    for mention in pattern.finditer(value):
                        if _ROLE.match(value[mention.end():]):
                            continue
                        accepted.add(identifier)
                        evidence.append(dict(field=field,start=clause.start()+mention.start(),
                            end=clause.start()+mention.end(),text=mention.group(),
                            settlement_id=identifier))
    report = BMTownReport(url=notice['url'],published_at=datetime.fromisoformat(notice['published_at']),
        event_settlement_ids=frozenset(accepted),fire_report=bool(accepted),title=title,description=description)
    return report, evidence
