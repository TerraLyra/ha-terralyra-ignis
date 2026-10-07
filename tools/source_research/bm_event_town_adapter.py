"""Experimental event-town evidence for satellite-first context, not geocoding."""
import re

_LOCATIVE = re.compile(r'(?:ban|ben|on|en|ön|án|én|nál|nél)$', re.I)
_NEAR = re.compile(r'[ \t]+(?:közelében|térségében|határában)\b', re.I)


def event_town_evidence(fields, settlements):
    """Require positive fire evidence and a local event-place construction.

    Unknown role alone is insufficient. Responders, corridors and ambiguous
    gazetteer names are not silently promoted. Original evidence is retained.
    """
    by_name = {}
    for place in settlements:
        by_name.setdefault(place.name, set()).add(place.identifier)
    accepted = []
    for field in ('title','description'):
        analysis = fields[field]
        text = analysis['text']
        fire_clauses = [e for e in analysis['fire_review']['evidence']
                        if e['kind']=='involved_candidate']
        for mention in analysis['role_review']['mentions']:
            start,end = mention['start'],mention['end']
            if text[start:end]!=mention['evidence']:
                raise ValueError('Mention evidence changed')
            if not mention['roles'] or any(h['role']!='unknown' for h in mention['roles']):
                continue
            if mention.get('linkage')!='lemma_or_exact' or len(mention['settlements'])!=1:
                continue
            name=mention['settlements'][0]
            identities=by_name.get(name,set())
            if len(identities)!=1:
                continue
            locative = mention['evidence'].casefold()!=name.casefold() and _LOCATIVE.search(mention['evidence'])
            if not locative and not _NEAR.match(text[end:]):
                continue
            clauses=[e for e in fire_clauses if e['start']<=start and end<=e['end']]
            for e in clauses:
                if text[e['start']:e['end']]!=e['evidence']:
                    raise ValueError('Fire evidence changed')
            if not clauses:
                continue
            accepted.append(dict(settlement_id=next(iter(identities)),field=field,
                                 start=start,end=end,evidence=mention['evidence'],
                                 basis='locative_in_positive_fire_clause',
                                 fire_evidence=clauses[0]['evidence']))
    return dict(event_settlement_ids=sorted({a['settlement_id'] for a in accepted}),
                evidence=accepted, incident_location_verified=False,
                creates_incident=False)


def report_from_current_notice(notice, fields, settlements, report_type):
    """Reject stale analyses before constructing a satellite context report.

    report_type is the pure BMTownReport class, injected to keep this offline
    research module independent of Home Assistant package initialization.
    No archive, manual review, observation or source text is modified.
    """
    from datetime import datetime
    if notice.get('description_status') == 'truncated':
        raise ValueError('Incomplete report text requires review')
    for field in ('title', 'description'):
        if fields[field]['text'] != notice.get(field, ''):
            raise ValueError('Analysis does not match the current report text')
    evidence = event_town_evidence(fields, settlements)
    return report_type(
        url=notice['url'], published_at=datetime.fromisoformat(notice['published_at']),
        event_settlement_ids=frozenset(evidence['event_settlement_ids']),
        fire_report=bool(evidence['evidence']),
        title=notice.get('title', ''), description=notice.get('description', ''),
    )
