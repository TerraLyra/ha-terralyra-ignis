"""Explicit TasALERT report view; no inferred ignition/extinction or satellite alert."""
ATTRIBUTION = 'TasALERT'
LICENSE_URL = 'https://creativecommons.org/licenses/by/4.0/'
TYPES = {'Bushfire':'bushfire', 'Fuel Reduction Burn':'planned_burn', 'Structure Fire':'structure_fire'}


def report_views(engine):
    """Only current, unambiguous incident points are candidates for map display."""
    views=[]
    for identifier,entry in sorted(engine.ledger.items()):
        record=entry['record'];fields=record['fields']
        if entry['presence']!='in_snapshot' or fields.get('feedType')!='incident' or record['point'] is None:
            continue
        views.append({'id':identifier,'title':record['name'],
                      'category':TYPES.get(fields.get('type'),'other'),
                      'source_type':fields.get('type'), 'source_status':fields.get('status'),
                      'latitude':record['point']['latitude'],'longitude':record['point']['longitude'],
                      'source_created_at':record['record_times'].get('created'),
                      'source_changed_at':record['record_times'].get('changed'),
                      'source_url':fields.get('url'), 'attribution':ATTRIBUTION,
                      'license_url':LICENSE_URL, 'transformation':'Filtered incident records; normalized coordinates and record timestamps.',
                      'official_report':True,'satellite_detection':False,
                      'active_fire_verified':False})
    return views
