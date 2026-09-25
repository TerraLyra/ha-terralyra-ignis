"""Offline label-impact assessment; synthetic coordinates, no runtime changes.

Compare the global cities500 baseline with an additive HU supplement. This
measures label changes, not label accuracy or real incident locations.
"""
import argparse
from collections import Counter
from contextlib import closing
import hashlib
import json
import math
from pathlib import Path
import sqlite3

from bm_bundled_places import DATABASE as BASE
from bm_hu_gazetteer import DATABASE as HU


def distance(a, b):
    lat1, lon1, lat2, lon2 = map(math.radians, (*a, *b))
    value = math.sin((lat2-lat1)/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin((lon2-lon1)/2)**2
    return 12742.0176 * math.asin(math.sqrt(min(1.0, max(0.0, value))))


def nearest(point, rows):
    if not rows:
        raise ValueError('Empty candidate set')
    # Stable baseline-first tie policy; supplemental ties never replace a label.
    return min(((distance(point, (r[1], r[2])), r) for r in rows), key=lambda pair: pair[0])


def compare(point, baseline, supplement):
    old_distance, old = nearest(point, baseline)
    new_distance, new = nearest(point, [*baseline, *supplement])
    return dict(latitude=point[0], longitude=point[1], before=old[0], after=new[0],
                before_km=round(old_distance, 3), after_km=round(new_distance, 3),
                changed=old[0] != new[0], selected_source=new[3])


def assess():
    with closing(sqlite3.connect(BASE.resolve().as_uri()+'?mode=ro', uri=True)) as db:
        # Includes neighbouring countries; deliberately do not force HU labels.
        baseline = [(n, lat, lon, 'cities500') for n, lat, lon in db.execute(
            'SELECT name,latitude,longitude FROM places ORDER BY name,latitude,longitude')]
    with closing(sqlite3.connect(HU.resolve().as_uri()+'?mode=ro', uri=True)) as db:
        supplement = [(n, lat, lon, code) for n, lat, lon, code in db.execute(
            'SELECT name,latitude,longitude,feature_code FROM hu_names ORDER BY geoname_id')]
    results = []
    for lat in (46.0, 46.5, 47.0, 47.5, 48.0):
        for lon in (16.5, 17.0, 17.5, 18.0, 18.5, 19.0, 19.5, 20.0, 20.5, 21.0, 21.5, 22.0):
            # Local pruning is exact if winner is within 50km: at these
            # latitudes any point outside this box is more than 50km away.
            local = [r for r in baseline if abs(r[1]-lat) <= 1 and abs(r[2]-lon) <= 1]
            if not local or nearest((lat, lon), local)[0] >= 50:
                raise ValueError('Baseline proximity bound not met; broaden assessment')
            results.append(compare((lat, lon), local, supplement))
    return dict(schema_version=1, sample='60 synthetic grid points; not clipped to national borders',
                accuracy_assessed=False, runtime_changed=False,
                attribution='GeoNames, CC BY 4.0',
                base_sha256=hashlib.sha256(BASE.read_bytes()).hexdigest(),
                supplement_sha256=hashlib.sha256(HU.read_bytes()).hexdigest(),
                supplemental_feature_counts=dict(Counter(r[3] for r in supplement)),
                changed_labels=sum(r['changed'] for r in results),
                changed_by_feature=dict(Counter(r['selected_source'] for r in results if r['changed'])),
                results=results)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    print(json.dumps(assess(), ensure_ascii=False, indent=2))
