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
    return {
        'text': text,
        'entities': [dict(text=e.text, start=e.start_char, end=e.end_char,
                          label=e.label_) for e in doc.ents],
        'tokens': [dict(text=t.text, start=t.idx, end=t.idx+len(t.text),
                        lemma=t.lemma_, pos=t.pos_, dependency=t.dep_,
                        head_start=t.head.idx) for t in doc],
        'incident_location_verified': False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
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
    print(json.dumps(dict(model=args.model, version=nlp.meta.get('version'),
                         license=nlp.meta.get('license'), input_sha256=hashlib.sha256(data).hexdigest(),
                         load_seconds=loaded-start, analysis_seconds=time.perf_counter()-loaded,
                         results=results), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
