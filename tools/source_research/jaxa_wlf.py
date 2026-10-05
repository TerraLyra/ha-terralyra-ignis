"""Offline WLF preflight only; no provider, transport or inferred column mapping."""
from dataclasses import dataclass
from datetime import datetime, timezone
import csv
import hashlib
import io

CUTOFF = datetime(2026, 2, 1, tzinfo=timezone.utc)
MAX_BYTES = 4 * 1024 * 1024
MAX_ROWS = 100_000
MAX_LINE = 8192


def eligible_observation_time(value: datetime | None) -> bool:
    """Check the observation instant, never download/processing time."""
    if not isinstance(value, datetime) or value.utcoffset() is None:
        return False
    return value.astimezone(timezone.utc) >= CUTOFF


@dataclass(frozen=True)
class WlfStructure:
    """Preserved headers and structural counts, not decoded fire observations."""

    sha256: str
    headers: tuple[str, str]
    row_count: int
    column_count: int | None
    semantics_verified: bool = False


def inspect_structure(payload: bytes) -> WlfStructure:
    """Inspect bounded UTF-8 CSV without guessing dates, units or field names.

    Header-only input is structurally accepted, but is NOT a confirmed empty
    observation product. Real samples must establish that upstream convention.
    """
    if len(payload) > MAX_BYTES:
        raise ValueError("WLF sample exceeds byte limit")
    text = payload.decode("utf-8-sig")
    if "\x00" in text:
        raise ValueError("WLF sample contains NUL")
    lines = text.splitlines()
    if len(lines) < 2 or not all(line.startswith("#") for line in lines[:2]):
        raise ValueError("WLF sample needs two comment headers")
    if any(len(line) > MAX_LINE for line in lines):
        raise ValueError("WLF sample exceeds line limit")
    count = 0
    width = None
    for line in lines[2:]:
        if not line.strip():
            continue
        if line.startswith("#"):
            raise ValueError("Unexpected WLF comment after headers")
        try:
            fields = next(csv.reader(io.StringIO(line), strict=True))
        except csv.Error as exc:
            raise ValueError("Malformed WLF CSV row") from exc
        if width is None:
            width = len(fields)
            if width < 2:
                raise ValueError("WLF row is not comma-separated")
        elif len(fields) != width:
            raise ValueError("Inconsistent WLF row width")
        count += 1
        if count > MAX_ROWS:
            raise ValueError("WLF sample exceeds row limit")
    return WlfStructure(hashlib.sha256(payload).hexdigest(),
                        (lines[0], lines[1]), count, width)
