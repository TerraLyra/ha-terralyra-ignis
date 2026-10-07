"""Score manually annotated offline probe results, not geographic accuracy.

Event-place coverage counts name recognition only, never correct event-role
assignment. Gold responders are settlement-level targets; extra candidates may
be districts and are reported for review rather than labelled false positives.
"""
import argparse
import json
from pathlib import Path


def score_roles(expected, row):
    """Optional exhaustive mention-role labels, keyed by field and source span."""
    if 'mention_roles' not in expected:
        return None
    targets = set()
    for item in expected['mention_roles']:
        field, start, end = item['field'], item['start'], item['end']
        if field not in ('title', 'description'):
            raise ValueError('Unknown annotation field')
        text = row[field]['text']
        if not isinstance(start, int) or not isinstance(end, int) or not 0 <= start < end <= len(text):
            raise ValueError('Invalid annotation span')
        if text[start:end] != item['evidence']:
            raise ValueError('Annotation evidence mismatch')
        targets.add((field, start, end, item['role']))
    predictions = set()
    for field in ('title','description'):
        for m in row[field]['role_review']['mentions']:
            for h in m['roles']:
                if h['role'] != 'unknown':
                    predictions.add((field,m['start'],m['end'],h['role']))
    return dict(matched=sorted(targets & predictions), missed=sorted(targets-predictions),
                extra=sorted(predictions-targets))


def score(gold, probe):
    rows = probe['results']
    if len(gold) != len(rows):
        raise ValueError('Gold and probe record counts differ')
    output = []
    for expected, row in zip(gold, rows):
        if expected['title'] != row['title']['text']:
            raise ValueError('Gold and probe order/title mismatch')
        mentions = [m for field in ('title','description')
                    for m in row[field]['role_review']['mentions']]
        names = {n for m in mentions for n in m['settlements']}
        responders = {n for m in mentions if any(h['role']=='responder' for h in m['roles'])
                      for n in m['settlements']}
        involvement = {c for field in ('title','description') for c in row[field]['fire_review']['involvement']}
        places = set(expected['event_places'])
        target_responders = set(expected['responders'])
        unlinked = [dict(field=field, start=m['start'], end=m['end'], evidence=m['evidence'])
                    for field in ('title','description') for m in row[field]['role_review']['mentions']
                    if not m['settlements'] and any(h['role']=='responder' for h in m['roles'])]
        output.append(dict(id=expected['id'], unlinked_responders=unlinked,
                           mention_role_comparison=score_roles(expected,row), event_names_found=sorted(places & names),
                           event_names_missed=sorted(places - names),
                           responders_found=sorted(target_responders & responders),
                           responders_missed=sorted(target_responders - responders),
                           extra_responder_candidates=sorted(responders-target_responders),
                           involvement_matches=involvement==set(expected['involvement'])))
    return dict(records=output, event_role_accuracy_assessed=False,
                extinguishing_accuracy_assessed=False,
                no_fire_verified=False)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('gold',type=Path)
    parser.add_argument('probe',type=Path)
    args=parser.parse_args()
    print(json.dumps(score(json.loads(args.gold.read_text()),json.loads(args.probe.read_text())),ensure_ascii=False,indent=2))
