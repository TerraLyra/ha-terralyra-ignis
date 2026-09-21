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
    raw_control=source.get('stage_of_control_status')
    warnings=list(record['metadata_warnings'])
    control={'OC':'out_of_control','BH':'being_held','UC':'under_control','EX':'extinguished'}.get(raw_control,'unknown') if isinstance(raw_control,str) else 'unknown'
    if control == 'unknown':
        warnings.append('unknown_stage_of_control_status')
    prescribed=source.get('fire_was_prescribed')
    prescribed_label=('not_reported' if prescribed in (None,-1) else
        'not_prescribed' if type(prescribed) is int and prescribed==0 else
        'prescribed' if type(prescribed) is int and prescribed in (1,2,3,4) else 'unknown')
    if prescribed_label == 'unknown':
        warnings.append('unknown_fire_was_prescribed')
    return record | dict(metadata_warnings=tuple(warnings),distance_km=distance,inside_radius=distance<=radius_km,
        stage_of_control=control,prescribed_status=prescribed_label,
        current_activity='not_established')


def match_locations(feature, locations):
    """Project a report against explicit enabled places, never a Home fallback.

    Locations use the HA monitored-location dictionary shape. The caller must
    supply validated configuration; reject ambiguous IDs and enabled flags here.
    Return no presentation when there is no matching enabled location.
    """
    locations = tuple(locations)
    seen = set()
    matches = []
    record = None
    for location in locations:
        identity = location.get('id')
        name = location.get('name')
        if (not isinstance(identity, str) or not identity.strip() or identity in seen
                or not isinstance(name, str) or not name.strip()
                or type(location.get('enabled')) is not bool):
            raise ValueError('Unambiguous monitored location required')
        seen.add(identity)
        if not location['enabled']:
            continue
        candidate = match_record(feature, latitude=location['latitude'],
            longitude=location['longitude'], radius_km=location['radius_km'])
        if candidate['inside_radius']:
            record = candidate
            matches.append(dict(location_id=identity, location_name=name,
                                distance_km=candidate['distance_km']))
    if not matches:
        return None
    matches.sort(key=lambda item: (item['distance_km'], item['location_id']))
    return record | dict(location_matches=tuple(matches),
        distance_km=matches[0]['distance_km'],
        distance_reference_id=matches[0]['location_id'],
        distance_reference_name=matches[0]['location_name'])
