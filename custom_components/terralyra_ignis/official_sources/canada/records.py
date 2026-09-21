"""Research-only projection preserving source values and time semantics."""
from datetime import datetime
import math
from .geometry import point_coordinates
from .identity import report_identity


def project_record(feature):
    p = feature['properties']
    lon, lat = point_coordinates(feature)
    # These timestamps have different meanings; none is inferred ignition time.
    times = {}
    for name in ('situation_report_date','status_date','record_start','record_end'):
        raw = p.get(name)
        stamp = datetime.fromisoformat(raw) if isinstance(raw,str) else None
        if stamp is None or stamp.utcoffset() is None:
            raise ValueError('Missing or naive ' + name)
        times[name] = stamp.isoformat()
    containment = p.get('percent_contained')
    warnings = []
    if containment is not None and containment != -1:
        if (type(containment) not in (int, float) or not math.isfinite(containment)
                or not 0 <= containment <= 100):
            warnings.append('invalid_percent_contained')
            containment = None
    else:
        containment = None
    return dict(identity=report_identity(feature),longitude=lon,latitude=lat,
        source_times=times, source_status=p.get('stage_of_control_status'),
        percent_contained=containment, metadata_warnings=tuple(warnings),
        raw_properties=dict(p), observation_completeness='not_established')
