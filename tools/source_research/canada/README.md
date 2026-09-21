# Canada CWFIF research client

Experimental tools outside `custom_components`. No HA entities, scheduler, user
location transmission or production activation. Tests use synthetic loopback HTTP
responses, never live upstream data. No live samples are included in this directory.

Install `requirements-test.txt` in an isolated environment, then run from repo root:

    python -m unittest discover -s tools/source_research/canada -v

The supported research path is `Controller(path, session).refresh()`, with one
controller owner per file and a caller-owned aiohttp session. It combines:
- a 30-second total network deadline, no redirects/compression, a 4 MB body bound;
- at most 2000 records, exact response-count agreement, validated point geometry,
  explicit timezone offsets and source-based identities;
- atomic pre-request reservation, retained successful data and persisted cooldown;
- one-hour successful refresh interval, exponential failure pauses, Retry-After;
- review holds for authentication/permanent HTTP errors and unreadable storage.

Intervals are conservative local choices, not documented service quotas. The
network deadline excludes synchronous parsing and disk writes. Multi-process file
locking is not implemented. Use a new dedicated research path, never a HA storage
file. `fetch.py` and `refresh_persisted` retain earlier synchronous research APIs
with socket timeouts only; they are not the deadline-enforced path.

`records.project_record` preserves source fields while treating containment -1 as
unknown. Source report/status times differ from record-validity times; neither a
fresh retrieval nor a current validity interval proves current fire activity.
Response completeness does not imply national coverage or an all-clear.

Before production: provider attribution and user presentation, location filtering,
unknown category policy, HA lifecycle and storage integration, compatibility and
migration review. See ../../../docs/CANADA_ADAPTER_READINESS.md.
