# ACT current-incidents readiness — 2026-09-16

Current status: experimental, disabled by default, research-only. Explicit test
markers are supported and are not a research blocker. Timestamp semantics remain
unverified; no production HA entities or calendars are connected. Earlier checkpoints
below are historical; the latest interpretation checkpoint supersedes their gates.

The [ESA source page](https://esa.act.gov.au/be-emergency-ready/warnings-alerts)
licenses Current Incidents and News Alerts under CC BY 4.0 with ESA attribution.
It documents a 60-second CAD update cadence and states that Current Incidents does
not supply warnings. CAP is a separate product; do not assume the same licence scope.

A bounded HTTPS request to https://esa.act.gov.au/feeds/currentincidents.xml returned
HTTP 200 and 5,685 bytes. The sample contained seven ambulance records and no fire
records. [Metadata](ACT_SAMPLE_METADATA_2026_09_16.json) retains only schema and
aggregate observations; no medical-event locations or identifiers are committed.

## Candidate adapter behavior

- Current Incidents supplies incident points, not warning polygons or thermal data.
- Use an explicit, verified vegetation-fire type mapping. Agency alone is not a fire
  classifier. Exclude ambulance/rescue events before any HA entity or history write.
- The sample provides `guid` and `cadid` with matching values. Cross-snapshot stability
  and conflict behavior remain unverified; never silently merge conflicting IDs.
- GeoRSS points use latitude then longitude, unlike GeoJSON. Validate range, finite
  coordinates and exact pair length before converting to the shared model.
- `resourceStatus` and `controlStatus` are separate fields. Preserve both rather than
  overwriting one; neither alone should become a general safety conclusion.
- Item `pubDate` differs from the description's `Updated` value. Publication time is
  not event revision or ignition time. `Time of Call` is not proven ignition time.
- Description dates have fractional seconds and no explicit offset; publication
  dates show AEST in this sample. Verify summer/DST behavior before assigning aware
  event times. Never replace missing source time with retrieval time.
- Bound XML bytes, nodes and item count; reject DTD/entity declarations and malformed
  envelopes. Show parse failures as failures, not a successful empty incident list.

## Next bounded development step

Obtain an official type dictionary or a permitted vegetation-fire sample and verify
source-time conventions. Then implement a pure, offline parser with synthetic tests
for mixed incident types, missing dates, timezone ambiguity, coordinate order,
conflicting IDs and hostile XML. Add the network client and optional calendar only
after parser checks pass. Existing location-based filtering can then be reused.

ACT can advance before Victoria/WA because current-incidents access and licence are
clearer. This is implementation readiness, not a change to wildfire-impact priorities.
No account or secret is needed for the successful request. No automatic feed polling,
CAP implementation, HA change, release or history deletion occurred in this review.

## Offline reader checkpoint

`tools/source_research/act_feed.py` now provides a bounded raw XML reader, outside
HA runtime code. It preserves uninterpreted fields, rejects malformed envelopes,
DTD/entity declarations, duplicate fields and excessive structures, and performs no
network or persistence. It is not yet an OfficialReport adapter or fire classifier.

Seven synthetic unittest cases passed with the system Python; the previously fetched
sample parsed as seven records. The default Homebrew Python could not load its expat
library, so that environment did not validate this code. No full HA suite was run.
Run: `python3 -m unittest discover -s tools/source_research -v`.

An [official ESA test notice](https://esa.act.gov.au/test-only-watch-and-act-grass-and-bushfire-4)
uses the type `GRASS AND BUSH FIRE`. It confirms that label exists, but is explicitly
a test, not a live incident or complete type dictionary. Test/exercise handling and
feed-level fire examples remain required before production classification.

## Offline classification checkpoint

`tools/source_research/act_classification.py` adds exact-label classification:
`GRASS AND BUSH FIRE` is a vegetation-fire candidate, `AMBULANCE RESPONSE` is
medical, and other or absent types remain unknown. A Fire agency or fire wording
in the title never overrides the source type. No claim of a complete taxonomy is made.

Standalone TEST/EXERCISE/DRILL words in title, description or type create a review
flag with the contributing field names. This conservative heuristic may flag ordinary
wording (including a negated test statement); it does not establish provider exercise
semantics. Absence of a marker remains not-established, never confirmed-real.
Candidates are not published, persisted or emitted as alerts.

All 14 synthetic research-reader/classification tests passed with system Python.
Production fire-feed samples, date semantics and reliable exercise metadata remain
open. These checks are separate from the full HA test suite.

## Offline time checkpoint

`tools/source_research/act_times.py` inspects publication, Updated and Time of Call
separately. It supports the observed local-clock formats and up to six fractional
second digits without depending on the machine's language. Missing, invalid and
repeated labels have distinct outcomes; original extracted values are retained.
Publication never substitutes for an absent update, and call time is not ignition.

Parsed values are explicitly naive wall-clock readings with timezone_unverified
status, not instants usable for ordering or freshness. AEST/AEDT labels are retained
but not converted until provider timezone behavior is verified. DST gap/fold clock
readings likewise remain unresolved. This module does not use HA timezone, receipt
time or the current clock. Unknown date formats remain invalid rather than guessed.

All 21 offline tests passed with system Python, including fractional seconds,
separate dates, duplicates, invalid calendars, missing data and unresolved DST times.
No production adapter or full HA-suite validation is implied.

## Offline identity/location checkpoint

`tools/source_research/act_identity.py` requires matching, nonempty `guid` and `cadid`
for a usable candidate ID. Missing, incomplete and conflicting pairs are distinct;
case is preserved. Repeated matching IDs are reported without merging records or
choosing a winner. This does not establish cross-snapshot stability or detect every
possible collision involving inconsistent ID pairs; those records remain conflicts.

GeoRSS coordinates are read latitude-first. Finite values within global bounds are
accepted; wrong-length pairs, malformed numbers and out-of-range values are rejected.
No swapping, clamping, Home-location fallback or invented coordinates is performed.
A valid coordinate does not prove the location is within ACT or spatially accurate.

All 28 synthetic offline tests passed using system Python. This remains research
code outside the HA runtime; production integration and source-time validation are
still pending. Existing history and live configuration are untouched.

## Combined offline inspection

`tools/source_research/act_summary.py` now runs the reader, classification,
identity/location checks and time inspection together. Its JSON-serializable output
contains only fixed diagnostic labels and counts. IDs, coordinates, titles and raw
dates are excluded. Malformed or over-limit XML raises an error before a summary is
returned. Counts across dimensions overlap and must not be added as incident totals.
Repeated-ID group counts cover matching guid/cadid pairs only.

All 34 offline tests passed with system Python. The previously retrieved sample was
also processed; see `ACT_OFFLINE_SUMMARY_2026_09_16.json`. This is a historical sample,
not a new live fetch or a current incident report. Empty or technically valid data
never establishes production readiness, absence of danger or confirmed active fires.

## Planned-burn classification follow-up — 2026-09-16

The [official ESA map page](https://esa.act.gov.au/?fullmap=true) exposes the type
`HAZARD REDUCTION BURN` in its incident listing. The retrieved page contains earlier
dates and an unavailable-updates message; this establishes a published label, not
current incident status or a new RSS sample. Its linked incident detail returned a
page-not-found message. No current wildfire or timezone specification was verified.

The offline classifier now maps only that exact normalized type to `planned_burn`,
separately from vegetation-fire candidates. Free-text mention of a planned burn does
not change another source type. Exercise flags remain independent. This classification
does not declare a burn safe, active, contained or complete, and suppresses no satellite
observations. Four added synthetic tests bring the offline suite to 38 passing tests.

## Source verification follow-up — 2026-09-16

A new bounded HTTPS read of Current Incidents returned HTTP 200 and 4,977 bytes:
six medical records, matching guid/cadid pairs, valid GeoRSS points, no repeated
matching IDs and no vegetation-fire records. All three time fields remained
`timezone_unverified`; exercise evidence remained `not_established`. The response
was processed in memory and only these aggregate observations were retained.
No raw medical records, identifiers or coordinates were saved.

Official non-test historical bushfire reports were verified on the ESA website:
[Corin Dam, January 2026](https://esa.act.gov.au/advice-bushfires-namadgi-national-park-stay-informed-corin-dam)
and [Mt Ainslie, February 2026](https://esa.act.gov.au/advice-grass-and-bushfire-northern-side-mt-ainslie-avoid-area).
Both are explicitly no longer current. Search excerpts associate the exact
GRASS AND BUSH FIRE label with these pages, but the opened page bodies do not
expose the structured type field. These are historical editorial reports, not
captured Current Incidents XML fixtures. They therefore strengthen contextual
evidence without closing the feed-level classification or exercise-metadata gates.

The official feed description still confirms Current Incidents licensing and its
CAD origin, but does not specify the timezone of Updated/Time of Call, DST fold/gap
handling, stable ID lifetime or machine-readable exercise discrimination. Targeted
search did not locate such a specification; this is not proof none exists.

Production ACT integration remains incomplete. No source timestamp is converted
by inference, no calendar event is created from retrieval time, and no enabled
HA entity or network polling is added. The independent source question list is in
[ACT_PROVIDER_QUESTIONS.md](ACT_PROVIDER_QUESTIONS.md). No message was sent to ESA.

## Experimental interpretation checkpoint — 2026-09-16 21:05 UTC

Per the current project decision, explicit test recognition is not a blocker.
The offline classifier retains the immutable original `ActItem` and adds tri-state
`is_test`: explicit TEST/TEST ONLY/NO ACTION REQUIRED (also EXERCISE/DRILL) wording
sets True; absent or recognized negated wording leaves None, never confirmed-real.
This is a review heuristic, not an upstream structured guarantee. It performs no
filtering: uncertain records and original text remain available. Aggregate research
logs continue to omit raw medical data; retaining source text in the parsed object
is not permission to publish or persist every feed record.

`act_time_interpretation.py` implements an explicit ACT-only Australia/Sydney rule
using stdlib ZoneInfo. It does not change raw inspection or infer HA/host timezone.
Winter/summer offsets follow the timezone database. Nonexistent clocks are rejected;
repeated clocks remain ambiguous unless a consistent AEST/AEDT label disambiguates.
Contradictory seasonal labels are reported, not silently corrected. Unique results
are marked `provider_interpretation_unverified`, even when a synthetic test passes.
CAP ISO timestamps with explicit offsets use that offset without a Sydney override;
their event meaning remains unverified. Raw input is retained in both paths.

Fresh sequential bounded reads (1 MiB each, 25-second request timeout, no redirects,
identity encoding) of GeoRSS/CAP/web returned HTTP 200, respectively 5,764 / 27,583 /
309,689 bytes. HTTP Date was 21:05:50 / 21:05:50 / 21:05:51 GMT; XML responses had no
Last-Modified or Age. Cache-Control was max-age 30 / 60 / 180, public. HTTP dates
identify response metadata, not incident time. No raw payloads were persisted.

RSS contained seven medical records. All inspected RSS clocks were offsetless
(description) or abbreviation-labelled (publication), with semantics unresolved.
CAP contained seven alerts; sent/effective/expires all had explicit +10:00 offsets.
Provisional guid-substring joins matched seven records: CAP sent equalled RSS call
wall time in seven, and RSS Updated in zero. This is not a verified identity join.
Exact raw RSS update/call strings did not appear in the fetched map HTML (zero
matches each); client rendering or different formatting remains possible, so no
web-display equivalence is claimed. Summer and transition source samples remain
missing. These findings do not promote the provider beyond experimental.

Synthetic winter, summer, gap, fold, seasonal-label conflict, explicit-offset and
missing-date tests pass. The complete source-research suite has 157 passing tests.
There are no ACT production imports, HA entities, calendars, polling, history writes
or releases. Research proceeds to Victoria while ACT evidence remains incomplete.
