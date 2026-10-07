"""Score manually annotated offline probe results, not geographic accuracy.

Event-place coverage counts name recognition only, never correct event-role
assignment. Gold responders are settlement-level targets; extra candidates may
be districts and are reported for review rather than labelled false positives.
"""
import argparse
import json
from pathlib import Path


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
        output.append(dict(id=expected['id'], event_names_found=sorted(places & names),
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
