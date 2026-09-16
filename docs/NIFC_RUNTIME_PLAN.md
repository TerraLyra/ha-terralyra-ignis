# NIFC runtime delivery plan

Status: proposed implementation contract after PR #22, 2026-09-16.
This file describes the next runtime change, not an enabled feature.

## What is actually ready

| Area | Verified result | Remaining limit |
| --- | --- | --- |
| Provider access | Bounded anonymous live queries, explicit WGS84, UTC fields | No complete terminal national retrieval verified |
| Parsing | UUID identity, separate WF/RX/CX, source times, complex links | A live complete parent/member graph is unverified |
| Retrieval | Byte/page/record limits, overall async deadline, cancellation | Must use HA-owned shared session and handle persistent truncation |
| Cooldown | Exponential waits, Retry-After, pause checkpoints | Fresh installation and deliberate recovery need runtime lifecycle handling |
| Persistence | Actual HA Store API exercised in isolated tests | No production Store key or ownership registration exists |
| Diagnostics | Fixed problem codes, six-language Repair helper | Helper has no production caller |
| Aggregates | 136 offline tests; no misleading active-fire totals | No entity or UI consumes the summary |

The full HA suite most recently verified before the summary change had 924 passing
tests; PR #22 also passed full CI. Test counts do not mean runtime activation.
Research remains in `tools/source_research`; production must not import that directory.

## First deliverable: opt-in diagnostic source status

Implement one diagnostic sensor per config entry, disabled in the entity registry by
default, using the existing QFD opt-in entity pattern. Its state describes retrieval
health (not requested, available, waiting, retained response, review required), never
fire danger or number of active fires. Attribute values contain aggregate source
record counts and separate receipt/source-time information, not incident identifiers
or coordinates. Do not call a source record "fresh" solely because it was downloaded.

No new calendar, map points, alerts or independent-fire total in this first deliverable.
This keeps a bounded first runtime change testable without guessing display semantics.

## Runtime implementation order and acceptance

1. Move the validated provider-specific primitives into a pure package under
   `official_sources/nifc/`. Keep research scripts as thin callers; avoid duplicate
   implementations. Adapt standalone imports, then run existing offline fixtures
   and HA tests against the same implementation. PUBLIC IP scope: adapter, basic
   normalization and HA plumbing only; no cross-source intelligence or scoring.
2. Add a client using the HA shared aiohttp session, explicit timeout/byte caps and
   disabled redirects. The client must not close the shared session. One shared
   source owner per HA instance excludes duplicate nationwide retrieval across entries.
   No monitored-location coordinates are sent to the service.
3. Add HA Store-backed cooldown ownership, with an explicit first-install path.
   Missing state is allowed only during known first initialization; corrupt or
   unexpectedly missing established state requires review. Preserve a durable pause
   before requests. Do not reuse any incident/history/archive storage key.
4. Add lifecycle unload and cancellation. Keep outstanding writes owned until settled;
   define how a hung write is reported and how shutdown avoids an unobserved task.
   Do not silently add arbitrary timeout cancellation around durable writes.
5. Register the disabled diagnostic entity. No request or background polling while
   disabled, unloaded, or without enabled monitored locations. Use a shared proposed
   15-minute refresh interval with cooldown enforcement; this is a client policy,
   not a published service rate allowance. Prevent manual refresh bypasses.
6. Connect fixed diagnostics to the existing Repair helper. Transient outage remains
   diagnostic; storage, schema and access failures pause. Recovery must be an explicit
   admin action after validation, without deleting history or shortening a valid
   server cooldown. Do not present a working recovery button before it exists.
7. Verify a complete bounded terminal response or diagnose why configured budgets
   cannot achieve it. Do not turn budget exhaustion into an available partial sensor.
   If a complete result cannot be obtained responsibly, reconsider query scope before
   activation instead of merely increasing limits.

Acceptance tests must cover two entries sharing one request; disabled/no-location
zero requests; shared session survival; missing/corrupt Store states; server cooldown
across reload; storage failures; cancellation/unload; issue isolation; and a separate
synthetic incident-history Store remaining unchanged. Full existing CI must pass.

## Later map/calendar scope

Use each monitored location's coordinates and radius, never Home as a fallback.
Missing coordinates remain unmatchable. Discovery and modification dates keep their
source meaning, with no inferred ignition date/duration. Complex containers and
members must not be counted together as independent fires. Missing parents remain
unresolved. A display-age threshold requires an explicit product decision; the
24-hour live sample diagnostic did not establish a production threshold.

## Release and operational boundary

First deliverable completion requires runtime tests, review of the actual diff and
an explicit deployment step. This plan neither creates a release nor enables NIFC in
live HA. Existing optimization remains paused. No migration, purge, source-expiry
closure or history deletion is authorized by this plan. Australia remains the first
regional priority; ACT/Victoria/WA gates and the global country screen are unchanged.

## Implementation checkpoint

The first extraction moves pure page/sequence validation, record normalization and
source-age/complex assessment into `official_sources/nifc/`. Research entry points
are compatibility wrappers, not copies. Standalone tests load only this pure package
under its canonical module name without importing HA setup; production uses normal
package imports and has no research-tool dependency. HA tests assert identical class
and function identity between the wrappers and integration-owned implementation.
Retrieval, lifecycle and summary extraction remain outstanding. No runtime activation.

## Network extraction checkpoint

The bounded query protocol, HTTP error type and asynchronous client now reside in
`official_sources/nifc/`; research entry points reuse them. `NifcClient` borrows a
caller-owned session and disables decompression/redirects per request without closing
or reconfiguring that session. HA tests cover success, HTTP failure and cancellation
using the actual HA session with synthetic responses. No runtime registration or
polling is added. Cooldown/coordinator extraction and enablement remain outstanding.
