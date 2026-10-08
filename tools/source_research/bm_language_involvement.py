"""Experimental clause-local fire evidence. Never current incident status.

Uses NLP lemmas but preserves source spans. Unknown relations stay unknown.
No production imports, network access or automatic report suppression.
"""
import re
from bm_reported_extinguishing import reported_extinguishing

_CATEGORIES = {'vegetation': {'aljnövényzet','növényzet','fű','erdő','bozót','avar','tarló'},
               'building': {'épület','melléképület','tanyaépület','ház','lakás','tároló'},
               'vehicle': {'autó','gépkocsi','jármű','kamion','kisbusz'}}
_BURN = {'ég','égett','kigyullad','gyullad','lángol'}


def review_involvement(analysis):
    text = analysis['text']
    tokens = analysis['tokens']
    for token in tokens:
        if text[token['start']:token['end']] != token['text']:
            raise ValueError('NLP evidence span mismatch')
    evidence = []
    # Contrast/conjunction boundaries prevent an adjacent threat or negation
    # from applying to every asset in a sentence. Decimal quantities are unused.
    for clause in re.finditer(r'[^.!?;,\n]+', text):
        local = [t for t in tokens if clause.start() <= t['start'] and t['end'] <= clause.end()]
        lemmas = {t['lemma'].casefold() for t in local}
        negative = bool(lemmas & {'nem','nincs'})
        uncertain = bool(lemmas & {'lehet','volna','feltételezett','gyakorlat','teszt'})
        categories = {c for c, words in _CATEGORIES.items() if words & lemmas}
        threat = 'veszélyeztet' in lemmas
        transfer = bool(lemmas & {'terjed','átterjed'}) and 'tűz' in lemmas
        burning = bool(lemmas & _BURN) or {'keletkezik','tűz'} <= lemmas
        def add(kind, category=None):
            evidence.append(dict(kind=kind, category=category, start=clause.start(),
                                 end=clause.end(), evidence=clause.group()))
        for category in sorted(categories):
            if negative or uncertain:
                add('uncertain_or_negated', category)
            elif threat:
                add('threatened', category)
            elif burning or transfer:
                add('involved_candidate', category)
            else:
                add('unknown', category)
    evidence.extend(dict(category=None, **e) for e in reported_extinguishing(text))
    involved = sorted({e['category'] for e in evidence if e['kind']=='involved_candidate'})
    return dict(involvement=involved,
                threatened=sorted({e['category'] for e in evidence if e['kind']=='threatened'}),
                reported_extinguishing=any(e['kind']=='reported_extinguished' for e in evidence),
                current_status_verified=False, requires_review=True, evidence=evidence)
