"""Research identity mapping. Preserve upstream IDs; no synthetic fallback."""
def report_identity(feature):
    props = feature.get('properties')
    if not isinstance(props, dict):
        raise ValueError('Missing properties')
    national = props.get('national_fire_id')
    agency = props.get('agency_code')
    if not isinstance(national, str) or not national.strip():
        raise ValueError('Missing national fire ID')
    if not isinstance(agency, str) or not agency.strip():
        raise ValueError('Missing source agency')
    return ('cwfif', agency, national)
