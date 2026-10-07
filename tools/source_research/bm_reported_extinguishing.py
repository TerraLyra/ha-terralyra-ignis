"""Bounded completed-extinguishing phrases; reports, not live incident state."""
import re

# Past finite forms only. Infinitives, present tense and plans are excluded.
_DONE = re.compile(r'\b(?:eloltott(?:ák|ak|a)|elfojtott(?:ák|ak|a)|oltott(?:ák|ak|a)[ \t]+el|fojtott(?:ák|ak|a)[ \t]+el)\b', re.I)
_OBJECT = re.compile(r'\b(?:tüzet|tűz|lángokat|lángok|lángot)\b', re.I)
_UNCERTAIN = re.compile(r'\b(?:nem|nincs|ne|ha|volna|talán|állítólag|próbált\w*|megpróbált\w*|gyakorlat\w*|teszt\w*)\b', re.I)

_HISTORICAL = re.compile(r'\b(?:tegnap|korábban|tavaly|múlt[ \t]+(?:héten|hónapban|évben))\b', re.I)
_CLAUSE = re.compile(r'[^,;]+?(?=[,;]|[ \t]+(?:de|azonban|viszont|és)[ \t]+|$)', re.I)


def reported_extinguishing(text):
    result = []
    # Sentence-level conservative veto intentionally favors missed positives
    # over incorrectly interpreting a conditional or negated completion.
    for sentence in re.finditer(r'[^.!?\n]+', text):
        part = sentence.group()
        if not _OBJECT.search(part):
            continue
        for clause in _CLAUSE.finditer(part):
            value = clause.group()
            if not _OBJECT.search(value):
                continue
            for match in _DONE.finditer(value):
                uncertain = bool(_UNCERTAIN.search(part))
                historical = bool(_HISTORICAL.search(part))
                quoted = any(c in part for c in ('"', '„', '“', '”', '«', '»'))
                kind = ('uncertain_extinguishing' if uncertain or quoted else
                        'historical_extinguishing' if historical else 'reported_extinguished')
                start = sentence.start()+clause.start()
                result.append(dict(kind=kind,
                                   start=start,end=sentence.start()+clause.end(),evidence=value,
                                   verb_start=start+match.start(),verb_end=start+match.end()))
    return result
