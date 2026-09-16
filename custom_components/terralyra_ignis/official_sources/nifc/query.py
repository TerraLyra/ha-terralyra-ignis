"""Bounded NIFC query protocol; no network or Home Assistant dependency."""
from __future__ import annotations
from dataclasses import dataclass
import json
from urllib.parse import urlencode
from .page import inspect_page
from .records import IncidentRecord, normalize_page

ENDPOINT = ('https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/'
            'WFIGS_Incident_Locations_Current/FeatureServer/0/query')


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key')
        result[key] = value
    return result


def _constant(value):
    raise ValueError('Non-finite JSON constant')


@dataclass(frozen=True)
class FetchResult:
    records: tuple[IncidentRecord, ...]
    page_count: int
    byte_count: int
    outcome: str
    snapshot_consistency: str = 'not_established'
    retrieval_method: str = 'offset_pagination'


def _fetch_steps(*, page_size=500, max_pages=20,
                    max_records=10000, max_page_bytes=1048576,
                    max_total_bytes=10485760, timeout=20) -> FetchResult:
    """Fetch explicit opt-in research data; no partial records on failure.

    Offset advances by requested page size, including short or empty continuation
    pages. A terminal report is not a consistent-snapshot guarantee. Missing flags,
    exhausted budgets, overlap and IRWIN conflicts abort without a result. Injected
    readers must enforce the byte cap while reading, not only after allocation.
    """
    for limit in (page_size, max_pages, max_records, max_page_bytes, max_total_bytes, timeout):
        if type(limit) is not int or limit <= 0:
            raise ValueError('Limits must be positive integers')
    if page_size > 2000:
        raise ValueError('Page size exceeds reviewed service limit')
    records, identities = [], set()
    byte_count, last_id = 0, None
    for index in range(max_pages):
        remaining = min(max_page_bytes, max_total_bytes - byte_count)
        if remaining <= 0:
            raise ValueError('Total byte budget exhausted')
        query = urlencode(dict(f='json', where='1=1',
            outFields='OBJECTID,IrwinID,IncidentTypeCategory,FireDiscoveryDateTime,ModifiedOnDateTime_dt,IsCpxChild,CpxID',
            returnGeometry='true', outSR=4326, orderByFields='OBJECTID ASC',
            resultOffset=index * page_size, resultRecordCount=page_size))
        payload = yield ENDPOINT + '?' + query, remaining, timeout
        if not isinstance(payload, bytes) or len(payload) > remaining:
            raise ValueError('Reader returned invalid or excessive payload')
        byte_count += len(payload)
        try:
            page = json.loads(payload.decode('utf-8'), object_pairs_hook=_pairs, parse_constant=_constant)
        except (UnicodeError, RecursionError) as error:
            raise ValueError('Invalid JSON encoding or nesting') from error
        inspection = inspect_page(page, max_records=page_size)
        if inspection.object_ids:
            if last_id is not None and inspection.object_ids[0] <= last_id:
                raise ValueError('Overlapping or reversed pages')
            last_id = inspection.object_ids[-1]
        current = normalize_page(page, max_records=page_size)
        if len(records) + len(current) > max_records:
            raise ValueError('Record budget exceeded')
        for record in current:
            if record.irwin_id in identities:
                raise ValueError('IRWIN identity conflict across pages')
            identities.add(record.irwin_id)
        records.extend(current)
        if inspection.continuation == 'terminal_reported':
            return FetchResult(tuple(records), index + 1, byte_count, 'terminal_reported')
        if inspection.continuation != 'more':
            raise ValueError('Unknown continuation')
        if len(records) >= max_records:
            raise ValueError('Record budget exhausted before terminal page')
    raise ValueError('Page budget exhausted before terminal page')



def _fetch_id_steps(*, page_size=100, max_pages=100, max_records=10000,
                    max_page_bytes=1048576, max_total_bytes=10485760, timeout=20):
    """Verify exact ID coverage and unchanged inventory, not an atomic snapshot.

    ArcGIS explicitly supports returnIdsOnly followed by objectIds subsets. Missing
    transfer flags are not used as evidence: every requested ID must be returned.
    An inventory change, omission, duplicate or exceeded budget rejects all records.
    """
    for limit in (page_size, max_pages, max_records, max_page_bytes, max_total_bytes, timeout):
        if type(limit) is not int or limit <= 0:
            raise ValueError('Limits must be positive integers')
    if page_size > 100 or max_records > 10000:
        raise ValueError('Inventory retrieval exceeds reviewed limits')
    byte_count = 0

    def request(params):
        nonlocal byte_count
        remaining = min(max_page_bytes, max_total_bytes - byte_count)
        if remaining <= 0:
            raise ValueError('Total byte budget exhausted')
        url = ENDPOINT + '?' + urlencode(dict(f='json', **params))
        if len(url) > 2400:
            raise ValueError('Request URL budget exceeded')
        payload = yield url, remaining, timeout
        if not isinstance(payload, bytes) or len(payload) > remaining:
            raise ValueError('Reader returned invalid or excessive payload')
        byte_count += len(payload)
        try:
            data = json.loads(payload.decode('utf-8'), object_pairs_hook=_pairs, parse_constant=_constant)
        except (UnicodeError, RecursionError) as error:
            raise ValueError('Invalid JSON encoding or nesting') from error
        if not isinstance(data, dict) or 'error' in data:
            raise ValueError('Invalid or error response')
        return data

    def inventory(data):
        ids = data.get('objectIds')
        flag = data.get('exceededTransferLimit', False)
        if (data.get('objectIdFieldName') != 'OBJECTID' or type(flag) is not bool or flag
                or not isinstance(ids, list) or len(ids) > max_records
                or any(type(oid) is not int or not 0 <= oid <= 2**53-1 for oid in ids)
                or len(set(ids)) != len(ids)):
            raise ValueError('Invalid or truncated ID inventory')
        return tuple(sorted(ids))

    ids = inventory((yield from request(dict(where='1=1', returnIdsOnly='true'))))
    if (len(ids) + page_size - 1) // page_size > max_pages:
        raise ValueError('Inventory exceeds page budget')
    records, identities = [], set()
    pages = 0
    for offset in range(0, len(ids), page_size):
        expected = ids[offset:offset+page_size]
        page = yield from request(dict(objectIds=','.join(map(str, expected)),
            outFields='OBJECTID,IrwinID,IncidentTypeCategory,FireDiscoveryDateTime,ModifiedOnDateTime_dt,IsCpxChild,CpxID',
            returnGeometry='true', outSR=4326, orderByFields='OBJECTID ASC'))
        inspection = inspect_page(page, max_records=page_size)
        if inspection.object_ids != expected or inspection.continuation == 'more':
            raise ValueError('Incomplete inventory batch')
        current = normalize_page(page, max_records=page_size)
        for record in current:
            if record.irwin_id in identities:
                raise ValueError('IRWIN identity conflict across batches')
            identities.add(record.irwin_id)
        records.extend(current)
        pages += 1
    final_ids = inventory((yield from request(dict(where='1=1', returnIdsOnly='true'))))
    if final_ids != ids:
        raise ValueError('Source inventory changed during retrieval')
    return FetchResult(tuple(records), pages + 2, byte_count, 'terminal_reported',
                       retrieval_method='verified_id_inventory')
