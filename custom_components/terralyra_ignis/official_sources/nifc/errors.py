"""NIFC HTTP errors without response payload retention."""
class SourceHTTPError(ValueError):
    """Status and Retry-After only; never retain response body or credentials."""
    def __init__(self, status, retry_after=None):
        super().__init__(f'Source HTTP status {status}')
        self.status = status
        self.retry_after = retry_after

