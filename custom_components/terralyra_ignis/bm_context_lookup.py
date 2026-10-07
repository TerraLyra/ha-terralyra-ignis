"""On-demand local BM context; execute SQLite work outside the HA event loop."""
from contextlib import closing
from datetime import datetime
from pathlib import Path
import sqlite3

from .bm_lightweight import lightweight_report
from .bm_satellite_context import bm_reports_for_satellite
from .report_context import IncidentContext, MAX_INCIDENTS, MAX_REPORTS

DATABASE = Path(__file__).with_name('data') / 'geonames_hu_names.sqlite3'


def lookup_context(incident_id, history, notices, resolver, database=DATABASE):
    """Recompute from current inputs, never write history or manual reviews."""
    if len(history) > MAX_INCIDENTS or len(notices) > MAX_REPORTS:
        raise ValueError('Context input exceeds limit')
    incidents, identities, names = [], {}, {}
    with closing(sqlite3.connect(Path(database).resolve().as_uri()+'?mode=ro',uri=True)) as db:
        metadata=dict(db.execute('SELECT key,value FROM metadata'))
        if metadata.get('source')!='GeoNames HU' or metadata.get('schema_version')!='1':
            raise ValueError('Unexpected settlement database')
        for item in history:
            incident=IncidentContext(item['track_id'],item['latitude'],item['longitude'],
                datetime.fromisoformat(item['first_seen']),datetime.fromisoformat(item['last_seen']))
            incidents.append(incident)
            place=resolver._resolve_sync(incident.latitude,incident.longitude)
            if place is None or place[1]!='HU':
                continue
            name,country,distance,lat,lon=place
            rows=db.execute('SELECT geoname_id,latitude,longitude FROM hu_names WHERE name=?',(name,)).fetchmany(2)
            # Reject homonyms anywhere in the supplement, not only this population.
            if len(rows)!=1 or rows[0][1:]!=(lat,lon):
                continue
            identity=f'geonames:{rows[0][0]}'
            identities[incident.incident_id]=frozenset({identity})
            names[identity]=name
    reports=[]
    rejected=0
    for notice in notices:
        try:
            report,_=lightweight_report(notice,names)
        except (ValueError,TypeError,KeyError):
            rejected+=1
            continue
        reports.append(report)
    result=bm_reports_for_satellite(incident_id,incidents,identities,reports)
    return {**result,'matching_method':'lightweight_local_rules',
            'notices_checked':len(notices),'invalid_notices':rejected,
            'article_pages_fetched':False}
