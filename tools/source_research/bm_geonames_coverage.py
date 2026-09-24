"""Offline coverage audit; never replaces the production gazetteer."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import zipfile

from bm_bundled_places import load_hungarian_places


def audit(archive_path: Path, names: list[str]) -> dict:
    """Inspect primary Hungarian populated-place names without emitting locations."""
    with zipfile.ZipFile(archive_path) as archive:
        info = archive.getinfo('HU.txt')
        if info.file_size > 50_000_000:
            raise ValueError('Country extract exceeds audit limit')
        raw = archive.read(info)
    counts = Counter()
    matches = {name: [] for name in names}
    for line in raw.decode('utf-8').splitlines():
        row = line.split('\t')
        if len(row) != 19:
            raise ValueError('Invalid GeoNames row')
        if row[8] != 'HU' or row[6] != 'P':
            continue
        counts[row[7]] += 1
        if row[1] in matches:
            matches[row[1]].append({'geoname_id': row[0], 'feature_code': row[7],
                                   'population': int(row[14] or 0)})
    bundled = {place.name for place in load_hungarian_places()}
    return {'source': 'GeoNames HU.txt', 'license': 'CC BY 4.0',
            'source_url': 'https://download.geonames.org/export/dump/HU.zip',
            'content_sha256': hashlib.sha256(raw).hexdigest(),
            'populated_feature_counts': dict(sorted(counts.items())),
            'requested_names': {name: {'in_bundle': name in bundled, 'country_records': records}
                                for name, records in matches.items()},
            'incident_location_verified': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('names', nargs='+')
    args = parser.parse_args()
    print(json.dumps(audit(args.archive, args.names), ensure_ascii=False, indent=2))
