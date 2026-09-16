"""Offline inspection of decoded NIFC point-query pages, not a network client."""
from dataclasses import dataclass


@dataclass(frozen=True)
class PageInspection:
    record_count: int
    continuation: str
    object_ids: tuple[int, ...]


def inspect_page(page: dict, *, max_records: int = 2000) -> PageInspection:
    """Check a page requested with OBJECTID ASC and outSR=4326.

    Explicit false means only that this response reports no further page. It does
    not prove a complete, consistent snapshot across changing server data. Missing
    transfer-limit metadata remains unknown, even for an empty or short page.
    Input must already have passed bounded JSON decoding. Geometry and incident
    attributes are not validated here, and IDs are for pagination, not durable identity.
    """
    if type(max_records) is not int or max_records <= 0:
        raise ValueError('Record limit must be a positive integer')
    if not isinstance(page, dict) or 'error' in page:
        raise ValueError('Invalid or error response')
    if page.get('objectIdFieldName') != 'OBJECTID' or page.get('geometryType') != 'esriGeometryPoint':
        raise ValueError('Unexpected layer schema')
    sr = page.get('spatialReference')
    if not isinstance(sr, dict) or type(sr.get('wkid')) is not int or sr['wkid'] != 4326:
        raise ValueError('Expected WGS84 output')
    if 'latestWkid' in sr and (type(sr['latestWkid']) is not int or sr['latestWkid'] != 4326):
        raise ValueError('Conflicting spatial reference')
    features = page.get('features')
    if not isinstance(features, list) or len(features) > max_records:
        raise ValueError('Missing or oversized feature list')
    ids = []
    for feature in features:
        if not isinstance(feature, dict) or not isinstance(feature.get('attributes'), dict):
            raise ValueError('Invalid feature')
        oid = feature['attributes'].get('OBJECTID')
        if type(oid) is not int or oid < 0 or (ids and oid <= ids[-1]):
            raise ValueError('Invalid, repeated or unordered object ID')
        ids.append(oid)
    flag = page.get('exceededTransferLimit')
    if 'exceededTransferLimit' not in page:
        continuation = 'unknown'
    elif type(flag) is not bool:
        raise ValueError('Invalid transfer-limit flag')
    else:
        continuation = 'more' if flag else 'terminal_reported'
    return PageInspection(len(features), continuation, tuple(ids))
