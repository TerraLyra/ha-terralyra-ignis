"""Experimental mention roles from local NLP evidence and a reviewed gazetteer.

No location promotion. Unmarked mentions remain unknown, including true event
mentions. Gazetteer matching by lemma is not geographic verification.
"""
import re

_RESPONDER = r'(?:tűzoltó(?:k|kat|i|it|inak|ság(?:a|ai|ának|át|ról|ból|hoz)?)?|egység(?:ek|ei|e|et|ét)?)'
_CONNECTORS = re.compile(r'^(?:\s|,|és\b|a\b|az\b|valamint\b|illetve\b|hivatásos\b|önkéntes\b|önkormányzati\b)*$', re.I)


def annotate_roles(analysis, settlements):
    text = analysis['text']
    tokens = analysis['tokens']
    names = {}
    for place in settlements:
        names.setdefault(place.name.casefold(), set()).add(place.name)
    mentions = []
    for token in tokens:
        start, end = token['start'], token['end']
        if text[start:end] != token['text']:
            raise ValueError('NLP evidence span mismatch')
        keys = {token['text'].casefold(), token['lemma'].casefold()}
        matches = set().union(*(names.get(k, set()) for k in keys))
        # Only propose adjectival linkage, never arbitrary suffix stripping.
        adjective = set().union(*(names.get(k[:-1], set()) for k in keys if k.endswith('i')))
        if matches or adjective:
            mentions.append(dict(start=start, end=end, evidence=text[start:end],
                                 settlements=sorted(matches or adjective),
                                 linkage='lemma_or_exact' if matches else 'adjective_candidate', roles=[]))
    for index, mention in enumerate(mentions):
        start, end = mention['start'], mention['end']
        roles = mention['roles']
        def evidence(role, a, b):
            roles.append(dict(role=role, start=a, end=b, evidence=text[a:b]))
        following = text[end:]
        responder = re.match(r'\s+(?:(?:hivatásos|önkéntes|önkormányzati)\s+)?'+_RESPONDER+r'\b', following, re.I)
        if responder:
            evidence('responder', start, end+responder.end())
        # Recognize a bounded shared-noun list, but never cross sentences.
        cursor = end
        for later in mentions[index+1:index+9]:
            if not _CONNECTORS.fullmatch(text[cursor:later['start']]):
                break
            cursor = later['end']
            tail = re.match(r'\s+(?:(?:hivatásos|önkéntes|önkormányzati)\s+)?'+_RESPONDER+r'\b', text[cursor:], re.I)
            if tail:
                evidence('responder', start, cursor+tail.end())
                break
        for entity in analysis['entities']:
            if entity['label']=='ORG' and entity['start']<=start and end<=entity['end']:
                evidence('organization', entity['start'], entity['end'])
        for role, pattern in [('direction', r'\s+felé\b'), ('street', r'\s+(?:utca\w*|út|úton|tér|téren)\b')]:
            match = re.match(pattern, following, re.I)
            if match:
                evidence(role, start, end+match.end())
        negation = re.search(r'\bnem\s+$', text[:start], re.I)
        if negation:
            evidence('negated', negation.start(), end)
        if not roles:
            evidence('unknown', start, end)
    return dict(mentions=mentions, incident_location_verified=False,
                event_location=None, requires_review=True)
