"""Bounded completed-extinguishing phrases; reports, not live incident state."""
import re

# Past finite forms only. Infinitives, present tense and plans are excluded.
_DONE = re.compile(r'\b(?:eloltott(?:ák|ak|a)|elfojtott(?:ák|ak|a)|oltott(?:ák|ak|a)[ \t]+el|fojtott(?:ák|ak|a)[ \t]+el)\b', re.I)
_OBJECT = re.compile(r'\b(?:tüzet|tűz|lángokat|lángok|lángot)\b', re.I)
_UNCERTAIN = re.compile(r'\b(?:nem|nincs|ne|ha|volna|talán|állítólag|próbált\w*|megpróbált\w*|gyakorlat\w*|teszt\w*)\b', re.I)


def reported_extinguishing(text):
    result = []
    # Sentence-level conservative veto intentionally favors missed positives
    # over incorrectly interpreting a conditional or negated completion.
    for sentence in re.finditer(r'[^.!?\n]+', text):
        part = sentence.group()
        if not _OBJECT.search(part):
            continue
        for match in _DONE.finditer(part):
            result.append(dict(kind='uncertain_extinguishing' if _UNCERTAIN.search(part)
                               else 'reported_extinguished',
                               start=sentence.start(),end=sentence.end(),evidence=part,
                               verb_start=sentence.start()+match.start(),
                               verb_end=sentence.start()+match.end()))
    return result
