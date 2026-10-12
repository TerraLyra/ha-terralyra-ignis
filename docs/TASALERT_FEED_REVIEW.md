# TasALERT feed preflight

Research only; no runtime provider, entities or calendar entries are enabled.

## Products and attribution

The supported products in scope are:

- https://alert.tas.gov.au/data/cap-au.xml
- https://alert.tas.gov.au/data/incidents-and-alerts.xml
- https://alert.tas.gov.au/data/incidents-and-messages.kml

Redistribution of these feeds is permitted under CC BY 4.0. Attribute TasALERT,
link the original product and https://creativecommons.org/licenses/by/4.0/,
and identify filtering or transformation. Preserve supplied attribution and
notices; do not imply endorsement. This scope does not automatically extend to
other products or linked pages. Permission correspondence is not part of this
repository.

## Single snapshot — 2026-10-12

All three requests returned HTTP 200. The CAP-named endpoint contained an
EDXL-DE 1.0 envelope, with no content objects or CAP alerts. Its distribution
clock was `2026-10-13T04:09:07+11:00`, equivalent to October 12 17:09:07 UTC.
The RSS 2.0 channel contained no items. Neither empty response establishes
absence of incidents: the KML response simultaneously contained 20 placemarks.

KML 2.2 snapshot:

- 14 `incident` records: 2 Bushfire, 11 Fuel Reduction Burn, 1 Structure Fire.
- 6 `burnt-area` records, separate from the incident records.
- Incident statuses: 12 Patrol, 2 Going. Preserve these source values.
- All 14 incidents had Point geometry; 17 placemarks had Polygon geometry.
  An individual placemark can contain both, nested in MultiGeometry.
- ExtendedData keys included created, changed, number, title, type, status,
  agency, address, feedType, url and burntArea.
- Observed created/changed timestamps carried `+00:00`. KML coordinates use
  longitude, latitude order. Never treat a polygon vertex as an incident point.

The CAP HTTP response advertised a ten-second cache lifetime and up to 86400
seconds stale-if-error. A cache header is not a permitted polling interval or a
freshness guarantee. HTTP receipt and Last-Modified do not date a fire.

## Implementation direction

Start with offline KML parsing. Keep original type, status, agency, ID, number,
created/changed clocks and source link. Treat created/changed as record clocks,
not proven ignition/extinction times. Require explicit offsets; do not guess.
Use incident Point geometry only for an initial point adapter. Retain the
existence of area geometry without manufacturing a centre or conflating a burnt
area with an active fire. Preserve IDs as strings; do not assume incident number
or placemark ID reuse rules from a single snapshot.

Keep Bushfire, Fuel Reduction Burn and Structure Fire distinct. Do not map
Patrol to extinguished, Going to a measured perimeter, or feed removal to
extinction. Unknown types/statuses require explicit handling rather than a
silent assumption. Do not combine CAP, RSS and KML as independent events.

## Remaining technical checks

- Synthetic parser tests: nested geometry, malformed/duplicate IDs, coordinate
  range and ordering, explicit winter/summer offsets, invalid or naive clocks,
  unknown types, missing fields, XML input bounds and unsafe source links.
- Compare later snapshots for identifier continuity and feed overlap, including
  an actual CAP content object and RSS item when available.
- Establish a conservative request policy with conditional retrieval and backoff;
  no polling interval is inferred from the license or cache lifetime.
- Validate update/removal behavior before production wiring. An empty feed or
  failed parse must not erase retained reports or claim the area is safe.

## Offline parser checkpoint

`tools/source_research/tasalert_kml.py` validates bounded UTF-8 KML without network
access. It rejects entity declarations, duplicate IDs/fields, unknown feed types,
unsafe source links, invalid points and offset-free supplied clocks. Unknown
incident statuses/types remain verbatim. Polygon-only burnt-area records remain
separate and receive no fabricated point. It does not implement retrieval,
persistence, lifecycle transitions or production entities.

Seven synthetic test cases pass, including winter/summer offsets and the two
explicit offsets for a repeated DST clock. The saved 2026-10-12 sample parsed as
14 incidents and six burnt-area records. This validates that snapshot's syntax,
not identifier lifetime, completeness or status semantics.

## Offline snapshot comparison

`tasalert_snapshot.compare_snapshots` validates both inputs before returning a
change plan. First-seen, unchanged, updated, not-in-snapshot and review-required
are observation states, not physical fire lifecycle states. Missing records retain
their prior representation in the plan; the comparator never deletes history or
infers extinction. A returned first-seen record need not be a newly ignited fire.

Identity-field changes, missing clocks, regressing update clocks and changed
content without an advancing update clock require review. Status strings remain
verbatim. Comparison does not persist state or perform automatic replacement;
a future consumer must handle review-required plans and parse errors explicitly.
Thirteen synthetic parser/comparison tests pass. Long-term retention, reappearance
across multiple snapshots and actual upstream identifier continuity remain open.

## Offline response policy

`tasalert_policy` is a pure state transition model, not an HTTP client. Its local
30-minute starting interval is a conservative engineering choice, not a documented
provider limit. Failures back off exponentially up to 24 hours; valid Retry-After
values can extend that deadline. An aware receipt clock and due-time gate are
required. ETags are sent only for an accepted representation; 304 without one is
an error. A 304 response establishes no observation freshness.

Malformed/empty responses and identity/clock/missing-record review signals keep
the previous accepted snapshot and validator. This first conservative model holds
the whole replacement, so unrelated updates may also be delayed pending review.
It has no expiry, disk persistence or production scheduling and must not be used
as a finished retention implementation. The next stage must address bounded
retention, operator recovery and partial-record reconciliation explicitly.

All 18 offline parser, comparison and response-policy tests pass. No additional
upstream requests were needed for these tests.

## Per-record reconciliation prototype

`tasalert_retention.reconcile` is a separate offline ledger prototype, not yet
connected to the response policy or persistent storage. An identity/clock conflict
holds that record while independent records update. Missing records remain labelled
not-in-snapshot and can expire after seven days during a validated nonempty update.
Seven days is a local research choice, not the event lifetime or a provider rule.
Reappearance refreshes presence without claiming a new ignition. Empty or invalid
feeds never trigger expiry. Persistent empty feeds therefore retain records; the
5000-record capacity fails closed rather than evicting unreviewed data. Records
held for review are not automatically replaced or purged.

23 offline tests pass across the four prototypes. Remaining integration work:
combine conditional-response and ledger acceptance without losing review state,
serialize receipt clocks and validators atomically, define operator recovery, and
validate fresh real snapshots. Runtime activation remains out of scope until these
boundaries are resolved.

## Offline response-state storage

`tasalert_storage` saves the accepted response bytes, validator, failure counter,
status and next-attempt deadline in a versioned, size-bounded file. It validates
before writing, flushes a same-directory temporary file and replaces the target
atomically. Failed replacement preserves the prior file. Corrupt/unknown versions
raise rather than silently clearing history or cooldown. This is a local prototype,
not HA Store integration, concurrent-writer coordination or a power-loss durability
guarantee. The separate per-record ledger is not yet serialized by this module.

26 offline tests pass, including restart cooldown/validator preservation, malformed
storage rejection and simulated replacement failure. No live HA files are accessed.

## Composed offline engine

`tasalert_engine.advance` now combines conditional-response policy and per-record
reconciliation. The accepted HTTP representation and retained report payloads are
separate: a valid response may contain a disputed record while other records update.
The disputed payload stays in the ledger with review diagnostics. A 304 preserves
those diagnostics and never refreshes last-seen clocks or expires missing records.
Invalid/empty responses keep both representations and their validator. Inputs are
not mutated. Expiry results belong only to the transition that performs expiry.

29 offline tests pass. The response-only storage module must not be used to persist
this composite engine: ledger and review persistence still need a single validated
storage envelope before restart-safe integration is possible. No runtime wiring
or automatic network requests are present.

## Composite restart checkpoint

`tasalert_engine_storage` now stores the accepted response and retained ledger in
one validated, bounded, versioned envelope using atomic replacement. Record shapes,
coordinates, clocks, IDs and review membership are validated before acceptance.
The stored HTTP representation may intentionally differ from a retained disputed
payload. Review diagnostics survive restart and 304; expiry actions do not replay.
32 offline tests pass. Earlier response-only storage remains a lower-level helper,
not the correct persistence entry point for a composite engine.

Still research-only: no HTTP client, HA Store integration, concurrency control,
operator recovery workflow or live activation. Real-world identity/status continuity
and persistence failure behavior in the eventual HA integration remain to validate.
