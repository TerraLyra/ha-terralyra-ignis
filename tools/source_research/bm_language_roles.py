"""Experimental mention roles from local NLP evidence and a reviewed gazetteer.

No location promotion. Unmarked mentions remain unknown, including true event
mentions. Gazetteer matching by lemma is not geographic verification.
"""
import re

_RESPONDER = r'(?:tűzoltó(?:k|kat|i|it|inak|ság(?:a|ai|ának|át|ról|ból|hoz)?)?|egység(?:ek|ei|e|et|ét)?)'


# Parse the list before linking its members to the gazetteer. Unlinked words
# remain surface evidence, not invented municipalities or coordinates.
_MODIFIER = r'(?:hivatásos|önkéntes|önkormányzati|létesítményi)'
_MEMBER = r'(?<!\w)(?!' + _MODIFIER + r'\b)[^\W\d_]+i\b'
_SEPARATOR = r'(?:[ \t]*,[ \t]*(?:(?:és|valamint|illetve)[ \t]+)?|[ \t]+(?:és|valamint|illetve)[ \t]+)(?:(?:a|az)[ \t]+)?'
_LIST = re.compile(r'(?<!\w)' + _MEMBER + r'(?:[ \t]+' + _MODIFIER + r')?(?:' + _SEPARATOR + _MEMBER + r'(?:[ \t]+' + _MODIFIER + r')?){1,15}[ \t]+' + _RESPONDER + r'\b', re.I)


def responder_lists(text):
    result = []
    for match in _LIST.finditer(text):
        members = [dict(start=match.start()+m.start(), end=match.start()+m.end(),
                        evidence=m.group()) for m in re.finditer(_MEMBER, match.group(), re.I)
                   if m.group().casefold() not in {'tűzoltói'}]
        result.append(dict(start=match.start(), end=match.end(), evidence=match.group(), members=members))
    return result


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
    groups = responder_lists(text)
    linked_spans = {(m['start'], m['end']) for m in mentions}
    for group in groups:
        for member in group['members']:
            if (member['start'], member['end']) not in linked_spans:
                mentions.append(dict(**member, settlements=[], linkage='unlinked_responder_member', roles=[]))
                linked_spans.add((member['start'], member['end']))
    mentions.sort(key=lambda m:m['start'])
    for mention in mentions:
        start, end = mention['start'], mention['end']
        roles = mention['roles']
        def evidence(role, a, b):
            roles.append(dict(role=role, start=a, end=b, evidence=text[a:b]))
        for group in groups:
            if any(m['start']==start and m['end']==end for m in group['members']):
                evidence('responder', group['start'], group['end'])
        following = text[end:]
        responder = re.match(r'\s+(?:(?:hivatásos|önkéntes|önkormányzati)\s+)?'+_RESPONDER+r'\b', following, re.I)
        if responder:
            evidence('responder', start, end+responder.end())
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
    corridors = []
    for left, right in zip(mentions, mentions[1:]):
        # Explicit adjacent linked names only. Do not jump across unknown text,
        # clauses, responders or street references to fabricate a corridor.
        if not left['settlements'] or not right['settlements']:
            continue
        if any(h['role'] != 'unknown' for m in (left,right) for h in m['roles']):
            continue
        if not re.fullmatch(r'[ \t]+és[ \t]+', text[left['end']:right['start']], re.I):
            continue
        tail = re.match(r'[ \t]+között\b', text[right['end']:], re.I)
        if not tail:
            continue
        end = right['end'] + tail.end()
        relation = dict(start=left['start'], end=end, evidence=text[left['start']:end],
                        endpoints=[left['settlements'],right['settlements']],
                        incident_geometry_verified=False)
        corridors.append(relation)
        for mention in (left,right):
            mention['roles'] = [dict(role='between_places',start=relation['start'],
                                     end=end,evidence=relation['evidence'])]
    return dict(mentions=mentions, corridors=corridors, incident_location_verified=False,
                event_location=None, requires_review=True)
