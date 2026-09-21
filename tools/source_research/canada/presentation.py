"""Research-only matching and labels; never classifies official warnings."""
import math
from records import project_record


def match_record(feature, *, latitude, longitude, radius_km):
    for value in (latitude,longitude,radius_km):
        if type(value) not in (int,float) or not math.isfinite(value):
            raise ValueError('Finite location required')
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180 or radius_km <= 0:
        raise ValueError('Invalid monitored location')
    record=project_record(feature)
    lat1,lat2=map(math.radians,(latitude,record['latitude']))
    dlat=lat2-lat1;dlon=math.radians(record['longitude']-longitude)
    a=math.sin(dlat/2)**2+math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    distance=6371.0088*2*math.asin(math.sqrt(max(0,min(1,a))))
    source=record['raw_properties']
    control={'OC':'out_of_control','BH':'being_held','UC':'under_control','EX':'extinguished'}.get(source.get('stage_of_control_status'),'unknown')
    prescribed=source.get('fire_was_prescribed')
    prescribed_label=('not_reported' if prescribed in (None,-1) else
        'not_prescribed' if type(prescribed) is int and prescribed==0 else
        'prescribed' if type(prescribed) is int and prescribed in (1,2,3,4) else 'unknown')
    return record | dict(distance_km=distance,inside_radius=distance<=radius_km,
        stage_of_control=control,prescribed_status=prescribed_label,
        current_activity='not_established')
