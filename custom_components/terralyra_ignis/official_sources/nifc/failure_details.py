"""Allowlisted failure descriptions; never persist arbitrary exception text."""

FAILURE_REASONS = frozenset({
    'Conflicting complex relationship',
    'Conflicting spatial reference',
    'Connection or response interrupted',
    'Date outside supported range',
    'Duplicate JSON key',
    'Duplicate incident identity',
    'Expected UTC epoch milliseconds',
    'Expected WGS84 output',
    'Expected bounded tuple of pages',
    'HTTP response rejected',
    'IRWIN identity conflict across batches',
    'IRWIN identity conflict across pages',
    'Incomplete inventory batch',
    'Invalid IRWIN identity',
    'Invalid JSON encoding or nesting',
    'Invalid WGS84 coordinate',
    'Invalid complex-child flag',
    'Invalid feature',
    'Invalid or error response',
    'Invalid or truncated ID inventory',
    'Invalid point',
    'Invalid transfer-limit flag',
    'Invalid, repeated or unordered object ID',
    'Inventory exceeds page budget',
    'Inventory retrieval exceeds reviewed limits',
    'Limits must be positive integers',
    'Missing IRWIN identity',
    'Missing or oversized feature list',
    'Nil IRWIN identity',
    'Non-finite JSON constant',
    'Overlapping or reversed page IDs',
    'Overlapping or reversed pages',
    'Page budget exhausted before terminal page',
    'Page size exceeds reviewed service limit',
    'Positive source-age threshold required',
    'Reader returned invalid or excessive payload',
    'Record budget exceeded',
    'Record budget exhausted before terminal page',
    'Record limit must be a positive integer',
    'Repeated IRWIN identity',
    'Request URL budget exceeded',
    'Request timed out',
    'Response byte limit exceeded',
    'TLS validation failure',
    'Timezone-aware assessment time required',
    'Timezone-aware source modification required',
    'Total byte budget exhausted',
    'Total record limit exceeded',
    'Total timeout must be a positive integer',
    'Unexpected HTTP response; automatic retry disabled',
    'Unexpected layer schema',
    'Unexpected page after terminal or unknown continuation',
    'Unexpected per-feature spatial reference',
    'Unknown continuation',
    'Unknown incident category',
    'Unrecognized validation failure',
})

def failure_reason(error):
    """Only exact, locally defined descriptions may leave the request boundary."""
    message = str(error)
    return message if message in FAILURE_REASONS else 'Unrecognized validation failure'

def validate_failure(reason, status):
    if not isinstance(reason, str) or reason not in FAILURE_REASONS:
        raise ValueError('Invalid saved failure reason')
    if status is not None and (type(status) is not int or not 100 <= status <= 599):
        raise ValueError('Invalid saved HTTP status')
