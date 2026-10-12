"""Project official reports into explicitly monitored places, locally."""
import hashlib
from .core.geo import haversine_km
from .official_sources.tasalert.presentation import report_views


def project_tasalert(state,locations):
    if state is None:return ()
    locations=tuple(locations)
    result=[]
    for item in report_views(state):
        matches=[]
        for loc in locations:
            if not loc.enabled:continue
            distance=haversine_km(loc.latitude,loc.longitude,item['latitude'],item['longitude'])
            if distance<=loc.radius_km:matches.append((distance,loc.id,loc.name))
        if matches:
            distance,identifier,name=min(matches)
            result.append({**item,'distance_km':distance,'distance_reference_id':identifier,
                           'distance_reference_name':name})
    return tuple(result)


def record_key(item):return hashlib.sha256(item['id'].encode()).hexdigest()


def record_title(item,language='en'):return 'TasALERT · '+item['title']


def record_attributes(item):
    return {**item,'source_url':item['source_url'] or 'https://alert.tas.gov.au/data/incidents-and-messages.kml',
            'report_category':item['source_type'],
            'source_modified_at':item['source_changed_at'],'source_freshness':'not_established','incident_text_status':'not_in_feed'}
