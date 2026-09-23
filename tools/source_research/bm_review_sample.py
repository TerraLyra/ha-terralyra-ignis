"""Evaluate a local JSON array of permitted plain-text RSS samples; no network."""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path

from bm_bundled_places import DATABASE, load_hungarian_places
from bm_location_candidates import review_locations

MAX_BYTES = 1024 * 1024


def evaluate_sample(raw: bytes, places=None) -> dict:
    if len(raw) > MAX_BYTES:
        raise ValueError('Sample exceeds 1 MiB')
    records = json.loads(raw)
    if not isinstance(records, list) or len(records) > 100:
        raise ValueError('Sample must be an array of at most 100 reports')
    if places is None:
        places = load_hungarian_places()
    results = []
    seen = set()
    for record in records:
        if not isinstance(record, dict):
            raise ValueError('Each report must be an object')
        if any(not isinstance(record.get(k), str) for k in ('title', 'description', 'source_url')):
            raise ValueError('title, description and source_url must be strings')
        truncated = record.get('input_truncated', False)
        if not isinstance(truncated, bool):
            raise ValueError('input_truncated must be a boolean')
        review = review_locations(record['title'], record['description'], record['source_url'],
                                  places, input_truncated=truncated)
        identity = hashlib.sha256(json.dumps([review.title, review.description,
                                             review.source_url], ensure_ascii=False).encode()).hexdigest()
        results.append({'content_sha256': identity, 'duplicate_in_sample': identity in seen,
                        'review': asdict(review)})
        seen.add(identity)
    return {'schema_version': 1, 'sample_sha256': hashlib.sha256(raw).hexdigest(),
            'report_count': len(results), 'distinct_content_count': len(seen),
            'accuracy_assessed': False, 'results': results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('sample', type=Path)
    args = parser.parse_args()
    with args.sample.open('rb') as stream:
        raw = stream.read(MAX_BYTES + 1)
    result = evaluate_sample(raw)
    result['gazetteer_sha256'] = hashlib.sha256(DATABASE.read_bytes()).hexdigest()
    result['gazetteer_attribution'] = 'GeoNames cities500, CC BY 4.0; https://www.geonames.org/'
    result['notice_attribution'] = 'BM OKF (for BM OKF notices supplied by the caller)'
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
