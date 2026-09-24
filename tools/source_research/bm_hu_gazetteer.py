"""Build and read the optional Hungarian GeoNames name-lookup supplement.

Research-only: no HA imports and no changes to the nearest-settlement database.
"""
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import zipfile

from bm_location_candidates import MAX_SETTLEMENTS, Settlement
from bm_bundled_places import REVIEWED_ALIASES, load_hungarian_places

DATABASE = Path(__file__).resolve().parents[2] / 'custom_components/terralyra_ignis/data/geonames_hu_names.sqlite3'
FEATURES = frozenset({'PPL', 'PPLA', 'PPLA2', 'PPLA3', 'PPLA4', 'PPLA5', 'PPLC', 'PPLL'})
MAX_PLACES = MAX_SETTLEMENTS
ALIASES = {**REVIEWED_ALIASES,
           'Gersekarát': ('Gersekaráton', 'gersekaráti'),
           'Somlóvásárhely': ('Somlóvásárhelyen', 'somlóvásárhelyi')}


def build(source: Path, destination: Path) -> None:
    """Atomically build a bounded, attributed supplement from official HU.zip."""
    with zipfile.ZipFile(source) as archive:
        info = archive.getinfo('HU.txt')
        if info.file_size > 50_000_000:
            raise ValueError('Country extract exceeds limit')
        raw = archive.read(info)
    places = []
    for line in raw.decode('utf-8').splitlines():
        row = line.split('\t')
        if len(row) != 19:
            raise ValueError('Invalid GeoNames row')
        if row[8] != 'HU' or row[6] != 'P' or row[7] not in FEATURES:
            continue
        identifier, latitude, longitude = int(row[0]), float(row[4]), float(row[5])
        if identifier <= 0 or not row[1].strip() or len(row[1]) > 160:
            raise ValueError('Invalid place identity')
        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            raise ValueError('Invalid place coordinates')
        places.append((identifier, row[1], row[7], row[10], latitude, longitude))
    if not places or len(places) > MAX_PLACES:
        raise ValueError('Country place count outside bounds')
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=destination.parent, suffix='.sqlite3', delete=False) as temporary:
        staging = Path(temporary.name)
    try:
        with closing(sqlite3.connect(staging)) as connection:
            connection.executescript('''
                CREATE TABLE hu_names (geoname_id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL, feature_code TEXT NOT NULL,
                    admin1_code TEXT, latitude REAL, longitude REAL);
                CREATE INDEX hu_names_name ON hu_names(name);
                CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            ''')
            connection.executemany('INSERT INTO hu_names VALUES (?,?,?,?,?,?)', sorted(places))
            connection.executemany('INSERT INTO metadata VALUES (?,?)', {
                'source': 'GeoNames HU', 'license': 'CC BY 4.0',
                'url': 'https://download.geonames.org/export/dump/HU.zip',
                'schema_version': '1', 'content_sha256': hashlib.sha256(raw).hexdigest(),
                'feature_codes': json.dumps(sorted(FEATURES)),
            }.items())
            connection.commit()
            connection.execute('VACUUM')
        staging.replace(destination)
    finally:
        staging.unlink(missing_ok=True)


def load_places(database: Path = DATABASE) -> tuple[Settlement, ...]:
    """Return name candidates with stable upstream IDs, never incident locations."""
    with closing(sqlite3.connect(database.resolve().as_uri() + '?mode=ro', uri=True)) as connection:
        metadata = dict(connection.execute('SELECT key,value FROM metadata'))
        if metadata.get('source') != 'GeoNames HU' or metadata.get('schema_version') != '1':
            raise ValueError('Unexpected Hungarian supplement')
        rows = connection.execute('SELECT geoname_id,name,feature_code FROM hu_names ORDER BY geoname_id').fetchmany(MAX_PLACES + 1)
    if not rows or len(rows) > MAX_PLACES:
        raise ValueError('Country place count outside bounds')
    if any(code not in FEATURES or not name.strip() or len(name) > 160 for _, name, code in rows):
        raise ValueError('Invalid supplement record')
    return tuple(Settlement('geonames:' + str(identifier), name, ALIASES.get(name, ()))
                 for identifier, name, _ in rows)


def load_review_places(database: Path = DATABASE) -> tuple[Settlement, ...]:
    """Expand name coverage, retaining legacy names excluded by country filtering.

    Exact-name matches use country records (including all their homonyms).
    Existing cities500-only names retain their old IDs; no new sublocalities
    are imported wholesale. This is name review, not coordinate reconciliation.
    """
    expanded = load_places(database)
    names = {place.name for place in expanded}
    retained = tuple(place for place in load_hungarian_places() if place.name not in names)
    if len(expanded) + len(retained) > MAX_PLACES:
        raise ValueError('Combined country place count outside bounds')
    return expanded + retained


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    build(args.source, args.destination)
