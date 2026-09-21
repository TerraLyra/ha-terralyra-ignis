"""In-memory research policy; intervals are local choices, not provider quotas."""
from dataclasses import dataclass
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from urllib.error import HTTPError, URLError


def retry_after(value, now):
    if not value:
        return None
    value = value.strip()
    if value.isascii() and value.isdigit():
        try:
            return (datetime.max.replace(tzinfo=now.tzinfo) if len(value) > 12
                    else now + timedelta(seconds=int(value)))
        except OverflowError:
            return datetime.max.replace(tzinfo=now.tzinfo)
    try:
        result = parsedate_to_datetime(value)
        return result if result.utcoffset() is not None and result > now else None
    except (ValueError, TypeError, OverflowError):
        return None


@dataclass
class RefreshState:
    last_success: object = None
    last_success_at: datetime | None = None
    next_attempt: datetime | None = None
    failures: int = 0
    status: str = 'initializing'
    review_required: bool = False

    def refresh(self, fetcher, now):
        if now.utcoffset() is None:
            raise ValueError('Aware clock required')
        if self.review_required or (self.next_attempt and now < self.next_attempt):
            return False
        server_retry = None
        try:
            result = fetcher()
        except HTTPError as error:
            server_retry = retry_after(error.headers.get('Retry-After') if error.headers else None, now)
            code = error.code
            error.close()
            if code in (401, 403) or (400 <= code < 500 and code not in (408, 429)):
                self.review_required = True
                self.status = 'review_required'
            else:
                self.status = 'rate_limited' if code == 429 else 'unavailable'
        except (URLError, TimeoutError, OSError):
            self.status = 'unavailable'
        except ValueError:
            self.status = 'invalid_response'
        else:
            self.last_success = result
            self.last_success_at = now
            self.failures = 0
            self.status = 'available'
            self.next_attempt = now + timedelta(hours=1)
            return True
        self.failures += 1
        delay = timedelta(minutes=5 * 2 ** min(self.failures - 1, 6))
        self.next_attempt = max(now + delay, server_retry or now)
        return False


def refresh_source(state, now):
    """Explicit caller owns scheduling; this function creates no background task."""
    from fetch import fetch
    return state.refresh(fetch, now)
