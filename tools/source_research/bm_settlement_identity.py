"""Offline identity bridge; settlement centres are never fire coordinates."""
from contextlib import closing
from pathlib import Path
import math
import sqlite3

from bm_hu_gazetteer import DATABASE, FEATURES, MAX_PLACES

CITIES = DATABASE.with_name('geonames_cities500.sqlite3')


def bridge_identity(name, country, latitude, longitude, records):
    """Join the selected cities500 record, not the satellite coordinates.

    Require identical name, HU country and centre coordinates. No nearest-name
    fallback: differing snapshots and duplicate records remain unresolved.
    """
    if not all(math.isfinite(v) for v in (latitude, longitude)):
        raise ValueError('Finite settlement centre required')
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        raise ValueError('Invalid settlement centre')
    if country != 'HU':
        return frozenset()
    matches = {f'geonames:{identifier}' for identifier, candidate, lat, lon in records
               if candidate == name and lat == latitude and lon == longitude}
    return frozenset(matches) if len(matches) == 1 else frozenset()


def load_records(database=DATABASE):
    with closing(sqlite3.connect(Path(database).resolve().as_uri()+'?mode=ro', uri=True)) as db:
        metadata = dict(db.execute('SELECT key,value FROM metadata'))
        if metadata.get('source') != 'GeoNames HU' or metadata.get('schema_version') != '1':
            raise ValueError('Unexpected gazetteer')
        rows = db.execute('SELECT geoname_id,name,latitude,longitude,feature_code FROM hu_names').fetchmany(MAX_PLACES+1)
    if not rows or len(rows) > MAX_PLACES or any(r[4] not in FEATURES for r in rows):
        raise ValueError('Invalid gazetteer records')
    return tuple(r[:4] for r in rows)


def audit():
    records = load_records()
    with closing(sqlite3.connect(CITIES.resolve().as_uri()+'?mode=ro', uri=True)) as db:
        rows = db.execute("SELECT name,country_code,latitude,longitude FROM places WHERE country_code='HU'").fetchall()
    matched = sum(bool(bridge_identity(*row, records)) for row in rows)
    return {'cities500_hu_records':len(rows), 'exact_identity_matches':matched,
            'unresolved':len(rows)-matched, 'production_enabled':False}


if __name__ == '__main__':
    import json
    print(json.dumps(audit()))
