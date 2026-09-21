"""Explicitly invoked research fetcher; no HA integration or automatic polling."""
import json
from urllib.parse import urlencode
from urllib.request import urlopen
from inspect_sample import inspect
from geometry import point_coordinates
from identity import report_identity

MAX_BYTES = 4_000_000
MAX_RECORDS = 2000
ENDPOINT = 'https://geoserver.cwfif.nrcan.gc.ca/geoserver/ows'


def decode_response(raw):
    if len(raw) > MAX_BYTES:
        raise ValueError('Response byte limit exceeded')
    def reject_constant(value):
        raise ValueError('Non-finite JSON constant')
    payload = json.loads(raw, parse_constant=reject_constant)
    if not isinstance(payload, dict):
        raise ValueError('Expected response object')
    features = payload.get('features')
    if not isinstance(features, list) or any(
        not isinstance(f, dict) or f.get('type') != 'Feature'
        or not isinstance(f.get('properties'), dict) for f in features
    ):
        raise ValueError('Malformed features')
    assessment = inspect(payload)
    features = payload['features']
    if len(features) > MAX_RECORDS or not assessment['response_count_complete']:
        raise ValueError('Incomplete or excessive response')
    if any(not issue.endswith(':percent_contained:unknown_sentinel') for issue in assessment['issues']):
        raise ValueError('Invalid record metadata: ' + ', '.join(assessment['issues'][:5]))
    for feature in features:
        point_coordinates(feature)
        report_identity(feature)
    return payload, assessment


def fetch(opener=urlopen):
    query = urlencode(dict(service='WFS', version='2.0.0', request='GetFeature',
        typeNames='public:cwfif_national_activefires', outputFormat='application/json',
        count=MAX_RECORDS, srsName='EPSG:4326', sortBy='national_fire_id A',
        CQL_FILTER='record_start<=now() AND record_end>now()'))
    with opener(ENDPOINT + '?' + query, timeout=30) as response:
        if response.status != 200:
            raise ValueError('Unexpected HTTP status')
        if response.headers.get_content_type() != 'application/json':
            raise ValueError('Expected JSON response')
        raw = response.read(MAX_BYTES + 1)
    return decode_response(raw)


if __name__ == '__main__':
    _, assessment = fetch()
    print(json.dumps(assessment, indent=2))
