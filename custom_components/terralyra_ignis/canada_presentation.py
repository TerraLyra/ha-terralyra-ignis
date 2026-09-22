"""Local official Canada report presentation, separate from satellite history."""
import hashlib
import json
from .core.locations import validate_monitored_locations
from .official_sources.canada.presentation import match_locations

SOURCE_URL = 'https://cwfis.cfs.nrcan.gc.ca/en/catalogue/results/bd641635-d30d-4b77-abc0-d6b59b1e8a00'
ATTRIBUTION = 'Canadian Forest Service / CWFIS / Natural Resources Canada'
LICENSE_URL = 'https://open.canada.ca/en/open-government-licence-canada'


def project_canada(result, locations):
    locations = tuple(locations)
    validate_monitored_locations(locations)
    if result is None:
        return ()
    features = result[0]['features']
    if len(features) > 2000:
        raise ValueError('Bounded validated response required')
    places = [location.as_dict() for location in locations]
    return tuple(item for feature in features
                 if (item := match_locations(feature, places)) is not None)


def record_key(item):
    # Keep arbitrary upstream identifiers out of entity-ID syntax.
    return hashlib.sha256(json.dumps(item['identity'], ensure_ascii=True).encode()).hexdigest()


def record_title(item, language='en'):
    label = 'Hivatalos tűzjelentés' if language == 'hu' else 'Official fire report'
    return f"Canada · {label} · {item['identity'][2]}"


def record_attributes(item):
    return {key: item[key] for key in (
        'identity', 'source_times', 'source_status', 'percent_contained',
        'metadata_warnings', 'location_matches', 'distance_reference_id',
        'distance_reference_name', 'stage_of_control', 'prescribed_status',
        'current_activity', 'observation_completeness')} | {
        'attribution': ATTRIBUTION, 'source_url': SOURCE_URL, 'license_url': LICENSE_URL,
        'source_freshness': 'not_established'}
