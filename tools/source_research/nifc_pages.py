"""Offline page-sequence validation, not a consistent-snapshot guarantee."""
from dataclasses import dataclass
from nifc_page import inspect_page


@dataclass(frozen=True)
class PageSequence:
    page_count: int
    record_count: int
    outcome: str
    snapshot_consistency: str = 'not_established'


def inspect_pages(pages: tuple[dict, ...], *, max_pages=20, max_records=10000,
                  max_page_records=2000) -> PageSequence:
    """Inspect an ordered sequence from one OBJECTID ASC query configuration.

    Caller must bound decoding bytes and preserve query/offset provenance. This
    function cannot prove no page was skipped or detect deletions between requests.
    It never returns incident records for persistence or removes existing history.
    """
    for limit in (max_pages, max_records, max_page_records):
        if type(limit) is not int or limit <= 0:
            raise ValueError('Limits must be positive integers')
    if not isinstance(pages, tuple) or len(pages) > max_pages:
        raise ValueError('Expected bounded tuple of pages')
    count, last_id = 0, None
    previous = None
    for page in pages:
        if previous is not None and previous != 'more':
            raise ValueError('Unexpected page after terminal or unknown continuation')
        result = inspect_page(page, max_records=max_page_records)
        count += result.record_count
        if count > max_records:
            raise ValueError('Total record limit exceeded')
        if result.object_ids:
            if last_id is not None and result.object_ids[0] <= last_id:
                raise ValueError('Overlapping or reversed page IDs')
            last_id = result.object_ids[-1]
        previous = result.continuation
    if not pages:
        outcome = 'no_pages'
    elif previous == 'terminal_reported':
        outcome = 'terminal_reported'
    elif previous == 'unknown':
        outcome = 'continuation_unknown'
    else:
        outcome = 'incomplete'
    return PageSequence(len(pages), count, outcome)
