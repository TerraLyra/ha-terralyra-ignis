"""Read-only research adapter for the existing IGNIS GeoNames database."""
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3

from bm_location_candidates import Settlement

DATABASE = Path(__file__).resolve().parents[2] / 'custom_components/terralyra_ignis/data/geonames_cities500.sqlite3'
# Small manually reviewed vocabulary, not a general Hungarian suffix generator.
REVIEWED_ALIASES = {
    'Szeged': ('Szegeden', 'szegedi'),
    'Vértesszőlős': ('Vértesszőlősön', 'vértesszőlősi'),
    'Tatabánya': ('Tatabányán', 'tatabányai'),
    'Nyíradony': ('Nyíradonyban', 'nyíradonyi'),
    'Nyírbátor': ('Nyírbátorban', 'nyírbátori'),
    'Debrecen': ('Debrecenben', 'debreceni'),
    'Egyek': ('Egyeken', 'egyeki'),
}


def load_hungarian_places(database: Path = DATABASE) -> tuple[Settlement, ...]:
    """No database writes, coordinate outputs or new dataset downloads.

    IDs are local content-derived IDs, not upstream GeoNames IDs (the bundled
    reduced database does not retain those). Distinct rows with the same name
    stay separate; exact duplicates are collapsed. IDs can change if data changes.
    """
    uri = database.resolve().as_uri() + '?mode=ro'
    with closing(sqlite3.connect(uri, uri=True)) as connection:
        metadata = connection.execute("SELECT value FROM metadata WHERE key='source'").fetchone()
        if metadata != ('GeoNames cities500',):
            raise ValueError('Unexpected bundled place database')
        rows = connection.execute(
            "SELECT DISTINCT name, admin1_code, latitude, longitude FROM places "
            "WHERE country_code='HU' ORDER BY name, admin1_code, latitude, longitude"
        ).fetchmany(5001)
    if len(rows) > 5000:
        raise ValueError('Hungarian place list exceeds review limit')
    result = []
    for row in rows:
        name = row[0]
        if not isinstance(name, str) or not name.strip():
            raise ValueError('Invalid bundled place name')
        digest = hashlib.sha256(json.dumps(row, ensure_ascii=False).encode()).hexdigest()
        result.append(Settlement('bundled-hu:' + digest, name, REVIEWED_ALIASES.get(name, ())))
    return tuple(result)
