"""Offline-testable bounded paging collector; caller supplies page retrieval.

No HTTP/HA dependencies. Offset paging cannot prove a stable upstream snapshot.
"""
import json
from spain_cyl_review import inspect_response, MAX_BYTES


def collect_pages(fetch_page, *, page_size=20, max_pages=5):
    if type(page_size) is not int or not 1 <= page_size <= 100:
        raise ValueError('Invalid page size')
    if type(max_pages) is not int or not 1 <= max_pages <= 5 or page_size * max_pages > 100:
        raise ValueError('Collection exceeds offline review bound')
    rows, seen = [], set()
    expected = None
    reason = 'page_limit'
    pages = 0
    received_bytes = 0
    for _ in range(max_pages):
        try:
            raw = fetch_page(len(rows), page_size)
            received_bytes += len(raw)
            if received_bytes > MAX_BYTES:
                reason = 'byte_limit'
                break
            review = inspect_response(raw)
        except (OSError, ValueError, TypeError):
            reason = 'page_error'
            break
        pages += 1
        total = review['total_count']
        if expected is None:
            expected = total
        elif total != expected:
            reason = 'total_changed'
            break
        page = [item['source'] for item in review['results']]
        if len(page) > page_size:
            reason = 'oversized_page'
            break
        keys = [json.dumps(r, sort_keys=True, ensure_ascii=False) for r in page]
        if any(k in seen for k in keys):
            reason = 'overlapping_pages'
            break
        if len(rows) + len(page) > total:
            reason = 'total_overrun'
            break
        rows.extend(page)
        seen.update(keys)
        if len(rows) == total:
            reason = 'count_reached'
            break
        if len(page) < page_size:
            reason = 'short_page'
            break
    # Count agreement is not snapshot consistency: equal-count changes can occur.
    return dict(results=rows, total_count=expected, pages_received=pages,
                count_complete=reason == 'count_reached', snapshot_verified=False,
                reason=reason)
