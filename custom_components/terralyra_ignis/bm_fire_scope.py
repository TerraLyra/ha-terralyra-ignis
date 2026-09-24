"""Conservative offline fire-scope clues, never automatic suppression or alerts."""
import re

# Deliberately bounded vocabulary. A match is evidence for human review only.
_PATTERNS = {
    'vegetation': r'(?<!\w)(?:erdő(?:tűz|ben)?|bozót(?:os)?|nádas|aljnövényzet|avar|száraz fű|tarló)(?!\w)',
    'local_asset': r'(?<!\w)(?:lakás(?:ban|tűz)?|ház(?:ban)?|családi ház|személyautó|gépkocsi|autó|jármű)(?!\w)',
    'fire': r'(?<!\w)(?:ég|égett|égnek|égették|lángol|lángolt|tűz|tüzet|tűz keletkezett|kigyulladt)(?!\w)',
    'accident': r'(?<!\w)(?:összeütközött|ütközött|karambolozott|karambol|baleset|elgázolt|felborult)(?!\w)',
    # Broad veto only: smoke, extinguishing and compounds must prevent a
    # non-fire label even when the narrow type classifier misses them.
    # Responding firefighters (tűzoltók) alone do not establish a fire.
    'possible_fire': r'(?<!\w)(?:\w*tűz\w*|\w*láng\w*|\w*füst\w*|kigyull\w*|meggyull\w*|leégett|kiégett|oltják|oltották|eloltották)(?!\w)',
    'area': r'(?<!\w)\d+(?:[,.]\d+)?[ \t]*(?:hektár(?:on|os|nyi)?|négyzetméter(?:en|es|nyi)?)(?!\w)',
    'uncertain': r'(?<!\w)(?:nem|nincs|veszély|veszélye|megelőzés|gyakorlat|teszt|feltételezett|lehet|lehetett|esetleg|téves)(?!\w)',
}
PATTERNS = {key: re.compile(value, re.IGNORECASE) for key, value in _PATTERNS.items()}


def review_fire_scope(title: str, description: str, *, input_truncated: bool = False) -> dict:
    """Retain evidence and unknown/mixed cases; area mentions are not burned area.

    Sentence-level co-occurrence is a clue, not semantic confirmation. No acreage
    threshold, active-fire status or fire extent is inferred from these patterns.
    """
    if not isinstance(title, str) or not isinstance(description, str):
        raise ValueError('Report fields must be strings')
    if len(title) > 2000 or len(description) > 4000:
        raise ValueError('Report exceeds bounds')
    evidence = []
    vegetation = local = uncertain = accident = fire_mentioned = False
    if not input_truncated:
        for field, text in (('title', title), ('description', description)):
            # Preserve decimal numbers when splitting sentences.
            for sentence in re.finditer(r'(?:\d[.,]\d|[^.!?\n])+', text):
                found = {}
                for kind, pattern in PATTERNS.items():
                    matches = list(pattern.finditer(sentence.group()))
                    if kind == 'possible_fire':
                        matches = [m for m in matches if not re.fullmatch(r'tűzoltó(?:k|kat|knak|khoz|kkal|ság|ságok|sági)?', m.group(), re.I)]
                    found[kind] = bool(matches)
                    for match in matches:
                        start, end = sentence.start()+match.start(), sentence.start()+match.end()
                        evidence.append(dict(kind=kind, field=field, start=start, end=end,
                                             evidence=text[start:end]))
                fire = found['fire'] or bool(re.search(r'(?<!\w)(?:erdőtűz|lakástűz)(?!\w)', sentence.group(), re.I))
                accident |= found['accident']
                fire_mentioned |= fire or found['possible_fire']
                vegetation |= fire and found['vegetation']
                local |= fire and found['local_asset']
                uncertain |= found['uncertain']
    category = 'unknown'
    if not uncertain and not input_truncated:
        if vegetation and local:
            category = 'mixed_fire_candidate'
        elif vegetation:
            category = 'vegetation_fire_candidate'
        elif local:
            category = 'local_asset_fire_candidate'
        elif accident and not fire_mentioned and description.strip():
            category = 'non_fire_report_candidate'
    return dict(category=category, evidence=evidence, requires_review=True,
                large_extent_verified=False, automatically_excluded=False,
                input_truncated=input_truncated)
