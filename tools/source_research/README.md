# Offline official-source research

These standard-library tools inspect supplied ACT RSS bytes. They are outside the
Home Assistant integration and do not fetch feeds, publish alerts or write history.

Run the synthetic tests from the repository root:

```sh
python3 -m unittest discover -s tools/source_research -v
```

The `Official source research` workflow runs the same suite on Python 3.11 and 3.14
without HA dependencies, source credentials, live feed requests or artifact uploads.

`act_summary.summarize_feed(payload)` returns aggregate diagnostic counts only.
Its result is JSON serializable; categories, exercise flags, identities, coordinates
and three source-time fields are independent dimensions, not additive event totals.
No raw source IDs, coordinates, titles or dates appear in the summary. Underlying
inspection helpers retain raw fields in memory and should not be logged as summaries.

A malformed or over-limit feed raises `InvalidFeed`; callers must not replace that
with a successful zero-count result. Default bounds are 1 MiB and 10,000 items.

Important limits:

- Fire classification is a narrow candidate mapping, not a complete type dictionary.
- Textual test markers are heuristic; an unmarked item is not confirmed real.
- Parsed dates are unresolved wall-clock readings, unsuitable for freshness checks.
- Matching IDs in one sample do not establish stability across time.
- Repeated matching IDs are counted, not merged; inconsistent ID pairs remain errors.
- Global coordinate validity does not establish ACT membership or spatial accuracy.

See `docs/ACT_ADAPTER_READINESS.md` for dated evidence and remaining production gates.

## NIFC query-page inspection

`nifc_page.inspect_page` checks an already decoded, bounded JSON point-query page
requested with OBJECTID ascending and outSR=4326. It rejects error envelopes,
invalid/repeated/unordered object IDs, excessive records and unexpected spatial
references. This is a page-envelope check, not full geometry/incident validation.
Its ID tuple is transient paging metadata, not a durable incident identity or a
privacy-filtered output suitable for publishing.

An explicit transfer-limit true means more results, even on a short/empty page.
Missing transfer-limit metadata remains unknown. Explicit false reports a terminal
response only: it does not certify a complete, consistent multi-page snapshot.
No network client, next-offset calculation or automatic history reconciliation exists.
Future retrieval must bound pages/bytes and handle changing source data; missing
records must never imply incident closure or trigger history deletion.

Reference: https://developers.arcgis.com/rest/services-reference/enterprise/query-feature-service-layer/
Validation: eight synthetic NIFC tests, 49 total offline tests passed locally. The
five-record live sample was correctly classified as requiring continuation. No
additional pages or full incident dataset were fetched.

`nifc_pages.inspect_pages` checks a supplied tuple of decoded pages with configurable
page, total-record and per-page limits. It rejects cross-page duplicate/reversed IDs,
error pages and pages after a terminal/unknown continuation. Missing terminal pages
remain incomplete; missing continuation metadata remains unknown. Empty intermediate
pages with an explicit continuation do not end the sequence.

The result reports counts and terminal status, never complete snapshot status.
The caller must retain query and offset provenance and bound JSON input bytes;
this checker cannot discover a skipped page from ID gaps, because IDs need not be
consecutive. Source changes between requests also remain unresolved. It performs no
network requests or history reconciliation. Eight sequence tests bring the complete
offline suite to 57 passing tests.


## NIFC incident records

`nifc_records.normalize_page` validates the page envelope and returns immutable
records with normalized IRWIN UUIDs, separate WF/RX/CX categories, WGS84 coordinates
and independent UTC discovery/modification dates. Missing/null dates and geometry
stay missing; malformed values and duplicate IDs reject the whole page. UUID syntax
is deliberately narrow; future schema differences require review, not guessed IDs.
No geometry means the record cannot be spatially matched yet. Valid global bounds
do not establish an accurate source position or membership in the USA.

This function does not certify completeness: retain `inspect_page` continuation
results and sequence checks separately. It does not check cross-page IRWIN conflicts,
complex membership, source-date ordering or freshness, or perform network/history
operations. The caller still bounds decoded input bytes. Discovery is not ignition.
See `docs/NIFC_ADAPTER_READINESS.md` for primary sources and remaining gates.

## Opt-in NIFC research retrieval

`nifc_fetch.fetch_incidents()` is an explicit network operation, outside HA runtime.
It requests only the reviewed official endpoint, with a fixed nationwide query,
OBJECTID order and WGS84 output; it sends no user coordinates or credentials.
Nothing fetches on import. There is no scheduler, CLI auto-run, persistence or retry.

Default limits: 500 records/page, 20 pages, 10,000 records, 1 MiB/page, 10 MiB total,
20-second socket timeout. The timeout is NOT a total wall-clock deadline: a slowly
streaming peer can extend runtime. A production asynchronous transport still needs
an overall deadline, cancellation, rate policy and explicit HA enablement design.
Redirects and compressed responses are refused. Bytes are capped during reading;
duplicate JSON keys, non-finite constants, malformed pages, repeated paging IDs and
cross-page IRWIN identities reject the operation. No partial records are returned
on failure. The injected-reader tests make no network requests.

The offset advances by the requested page size, even for short/empty continuation
pages. Unknown continuation and exhausted budgets fail closed. A terminal response
reports only the server's pagination end; concurrent source changes can still cause
missed records. It must never trigger deletion or closure of retained incidents.
No guarantee of national completeness, freshness or fire safety is made.

Validation: 76 synthetic offline tests pass, including ten retrieval tests. The
network transport was tested with mocked responses, not a live multi-page crawl.

## Cancellable research retrieval

`await nifc_async.fetch_incidents_async()` adds an overall 60-second asynchronous
network deadline across every page and streamed body. It reuses the synchronous
validator through a request generator, so identity, pagination and budget rules
cannot drift between implementations. The default transport requires aiohttp;
the standard-library offline tests inject readers and need no additional package.
The aiohttp session is scoped to the operation, refuses redirects/compression, does
not inherit proxy credentials and closes on cancellation. No request runs on import.

Cancellation and timeouts are cooperative: an injected reader must not block the
event loop or suppress cancellation. Bounded synchronous JSON validation cannot be
preempted, so this is not a hard real-time CPU deadline. The older synchronous entry
point remains socket-timeout-only. Neither path retries automatically; HTTP 429 and
5xx abort the operation. A scheduled production client still needs a provider-aware
cooldown/backoff policy; this tool creates no scheduler or HA integration.

Validation: 81 offline tests pass, including overall deadline, external cancellation,
shared multi-page validation and failure without retry/partial output. The default
aiohttp transport has not yet been verified with a live multi-page source request.
Reference: https://docs.aiohttp.org/en/stable/client_reference.html

The subsequent bounded live check exercised the actual aiohttp transport on two
five-record pages; both required continuation, and the record cap correctly aborted
the operation. No terminal-page or national completeness claim is made. Four more
synthetic transport tests bring the suite to 85 passing tests (Python 3.9 and 3.13).
See the dated live verification in `docs/NIFC_ADAPTER_READINESS.md`.

## Refresh policy prototype

`nifc_refresh` provides pure state transitions only: it does not schedule or issue
requests, enable HA entities, persist cache/history or automatically classify all
transport exceptions. The caller must distinguish transient failures, rate limits,
invalid data and access denial. Cancellation is not a failure transition.

Engineering defaults (not published NIFC request-rate permission): 15 minutes after
successful retrieval; transient failure delays of 15, 30, 60, 120, 240, then at most
360 minutes. Retry-After seconds or timezone-aware HTTP dates can extend this wait;
existing cooldowns are never shortened. Invalid data/access denial require manual
review. `due` also requires explicit enablement and no in-flight request; a future
coordinator must enforce that check atomically. There is no background retry loop.

All failure transitions retain the exact last successful result and its receipt
time. A successful terminal empty response is a latest-response cache update, NOT
incident-history deletion. Retrieval success does not establish source freshness or
snapshot consistency. The in-memory monotonic deadline cannot be serialized across
process restarts; restart-safe cooldown persistence remains future work.

The async transport preserves HTTP status and Retry-After in a typed error without
retaining response bodies. The synchronous research transport is unchanged.
Reference: https://www.rfc-editor.org/rfc/rfc9110.html#name-retry-after

## Explicit research coordinator and cooldown checkpoints

`ResearchCoordinator.refresh(enabled=True)` connects the policy to the async fetcher.
Enablement defaults to false. A single instance on one event loop excludes overlapping
requests; callers arriving during a request skip instead of queuing. Cancellation
propagates without changing state. Known HTTP, timeout, connection and validation
failures update cooldowns while retaining the previous response. Unexpected programming
errors propagate. TLS validation errors stop eligibility for review.

`checkpoint` exports only cooldown metadata; `restore_checkpoint` restores it against
a new process monotonic clock. The full saved remaining wait is applied again, ignoring
time spent offline to avoid shortening it due to wall-clock changes. This can delay a
refresh longer than necessary. Corrupt metadata raises an error; it is not a fresh-start
signal. These helpers do not write files: atomic durable storage, handling missing
checkpoints, restart orchestration and cache restoration remain unimplemented.
The checkpoint contains no incident records or user history. It must be saved after
state transitions by a future storage adapter. Cross-instance/process locking and a
HA scheduler are also outside this prototype. No background work starts on import.

Validation: 103 synthetic tests cover concurrency, cancellation, failure retention,
clock-independent cooldown restoration and malformed checkpoints.

## Explicit cooldown file storage

`nifc_storage.save_cooldown(directory, state, now=...)` writes only the fixed
`nifc-research-cooldown.json` name in an existing trusted application-owned directory.
It validates metadata, writes a private temporary file, flushes/fsyncs its contents,
and atomically replaces the checkpoint. Replacement failure leaves the previous file
intact. Only the operation's own temporary file is cleaned up. Symlink targets are
rejected; this is not a hardened interface for directories controlled by other users.

`load_cooldown` reads at most 4 KiB plus an overflow byte and validates the schema.
Missing, duplicate-key, malformed and oversized checkpoints raise errors rather than
resetting eligibility. First-time initialization must be an explicit caller decision.
This module does not read or write incident records/history. It is not yet wired to
the coordinator lifecycle: loading before enablement, saving after transitions and
handling save failures remain the caller's responsibility. No HA storage is touched.

A real subprocess test verifies that a new process restores the saved wait against a
new monotonic-clock origin. Other tests cover replacement failure, unrelated history
preservation, manual pause and corrupt files. All 109 offline tests passed locally on
Python 3.9 and 3.13. Directory metadata is not fsynced, so sudden-power-loss durability
is not claimed. Cross-process writers and automatic restart orchestration remain open.

## Persistent research lifecycle

`PersistentResearchCoordinator` now connects loading and saving to explicit refresh
calls. Construction requires an existing valid checkpoint; initial setup is an
explicit `save_cooldown` call with a chosen initial state. Missing/corrupt state never
silently enables requests. Each eligible request first saves a manual-pause marker,
then fetches and saves the resulting cooldown. If interrupted after that marker, a
restart stays paused for review. Normal success/transient failure replaces the marker
with the policy wait. Cancellation does not immediately retry.

Preflight save failure prevents network access and pauses the current instance.
Final save failure retains the previous in-memory response and leaves the persisted
pause marker. Exceptions propagate; callers must surface them. The guarantee assumes
atomic filesystem replacement, not power-loss durability. If a preflight save fails,
no new marker was committed; durable recovery of that storage failure is not claimed.
One owner per directory is required; separate processes are not mutually excluded.

This is still research tooling: synchronous file I/O must be adapted before use on
HA's event loop. There is no scheduler, HA activation, incident-history persistence or
automatic manual-pause reset. Seven lifecycle tests bring the offline suite to 116
passing tests on Python 3.9 and 3.13, including save failures, restart cooldowns,
cancellation, concurrency and disabled behavior. No live requests run in these tests.

## Async store interface prototype

`AsyncStoredResearchCoordinator` accepts an injected store with `async_load` and
`async_save`, matching the interface used by the integration's existing archives.
Explicit setup validates saved state; no implicit initialization is performed.
The lifecycle awaits storage instead of doing file I/O on the event loop. Production
HA Store has not been wired in: tests use asynchronous in-memory stores only.

A shielded save retains coordinator ownership until the write settles even when its
caller is cancelled, preventing an older write from racing a subsequent request.
A permanently hung store can delay cancellation; production storage recovery remains
open. No cross-process ownership or power-loss guarantee is introduced.

Diagnostics expose only fixed problem codes, in-flight state, a previous-response
presence flag and failure count. They never include source records, paths or raw
exception text, and never equate retrieval success with source freshness. These are
not yet translated HA Repair issues or automatic recovery actions.

121 offline tests passed locally, including asynchronous storage lifecycle, restart
cooldown, cancellation during writes, failed loading/saving and event-loop progress.

## Source age and complex relationships

The research query now requests documented IsCpxChild/CpxID fields. Normalization
preserves unknown membership, validates 0/1 flags and UUID parents, and rejects
self-links or explicit non-child/parent contradictions. A missing parent is unresolved.

`nifc_assessment.source_age` requires an explicit positive age threshold and aware
assessment time. It distinguishes missing, future, within-threshold and older source
modification times. Receipt time is never substituted. Record modification is not
fire observation time or proof of active fire. No display threshold is selected.

`complex_roles` labels containers, linked members, absent parents and conflicts
without merging/deleting records or producing independent-fire totals. Nested complex
relationships remain unresolved. Input must be normalized with unique incident IDs.
128 tests pass locally on Python 3.9 and 3.13. Expanded live-query compatibility and
production display policy are not yet verified or implemented.

## Aggregate display preparation

`nifc_summary.summarize` consumes a normalized refresh cache and explicit display
thresholds. It reports source-record counts by category, modification age and complex
role, plus missing location/discovery-time counts. These are overlapping dimensions,
not additive independent-fire totals. It exposes no raw IDs, coordinates or source
dates. No records are filtered, merged, persisted or deleted.

No cached response has a null record count; a terminal empty response has zero source
records but no asserted active-fire count. National completeness always remains
unestablished. Retrieval age and source modification age are separate. Retained data
after a failed refresh is explicitly labeled; no receipt-time fallback makes old
source records current. Both age thresholds are caller inputs, not selected defaults.

136 offline tests pass on Python 3.9 and 3.13. This is a display-data prototype, not
an HA sensor/calendar/dashboard or a fire-warning decision. Production UI, location
matching and end-to-end source activation remain outstanding.

## Integration-owned pure primitives

Page and sequence validation, record normalization and source-age/complex assessment
now live in `custom_components/terralyra_ignis/official_sources/nifc/`. The original
research modules re-export those implementations. The standalone loader uses the
canonical package name without importing HA setup; it is research-only. Production
must use ordinary relative imports and never depend on tools/source_research.
All existing 136 offline tests still pass on Python 3.9 and 3.13 after extraction.
