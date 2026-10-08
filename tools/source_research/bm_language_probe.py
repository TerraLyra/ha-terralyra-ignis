"""Offline NLP evidence probe; no event-location promotion or network calls.

Run in a separate environment with an explicitly installed HuSpaCy model.
Output retains spans and parses for manual role review, not production labels.
"""
import argparse
import hashlib
import json
import time
from pathlib import Path


def analyze(nlp, text):
    doc = nlp(text)
    result = {
        'text': text,
        'entities': [dict(text=e.text, start=e.start_char, end=e.end_char,
                          label=e.label_) for e in doc.ents],
        'tokens': [dict(text=t.text, start=t.idx, end=t.idx+len(t.text),
                        lemma=t.lemma_, pos=t.pos_, dependency=t.dep_,
                        head_start=t.head.idx) for t in doc],
        'incident_location_verified': False,
    }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--roles', action='store_true', help='Experimental gazetteer-linked role hints')
    parser.add_argument('--model', default='hu_core_news_md')
    args = parser.parse_args()
    data = args.input.read_bytes()
    records = json.loads(data)
    if not isinstance(records, list) or len(records) > 100:
        raise ValueError('Expected at most 100 records')
    for r in records:
        if not isinstance(r, dict) or any(not isinstance(r.get(k), str) or len(r[k]) > 6000
                                         for k in ('title', 'description')):
            raise ValueError('Expected bounded title and description strings')
    import spacy
    start = time.perf_counter()
    nlp = spacy.load(args.model)
    loaded = time.perf_counter()
    results = [dict(title=analyze(nlp, r['title']), description=analyze(nlp, r['description']))
               for r in records]
    if args.roles:
        from bm_hu_gazetteer import load_review_places
        from bm_language_roles import annotate_roles
        from bm_language_involvement import review_involvement
        from bm_event_town_adapter import event_town_evidence
        places = load_review_places()
        for result in results:
            for field in ('title', 'description'):
                result[field]['role_review'] = annotate_roles(result[field], places)
                result[field]['fire_review'] = review_involvement(result[field])
            result['satellite_context_evidence'] = event_town_evidence(result, places)
    print(json.dumps(dict(model=args.model, version=nlp.meta.get('version'),
                         license=nlp.meta.get('license'), spacy_version=spacy.__version__,
                         research_code_sha256={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                            for name in ('bm_language_probe.py','bm_language_roles.py','bm_language_involvement.py','bm_reported_extinguishing.py','bm_event_town_adapter.py')},
                         input_sha256=hashlib.sha256(data).hexdigest(),
                         load_seconds=loaded-start, analysis_seconds=time.perf_counter()-loaded,
                         results=results), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
