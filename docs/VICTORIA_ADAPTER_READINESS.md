# Victoria developer feed readiness — 2026-09-16

Status: reachable research candidate; not enabled or implemented.

## Evidence

The [CFA developer-feed page](https://www.cfa.vic.gov.au/rss-feeds) publishes
the JSON endpoint and identifies EMV as the developer-access manager. A bounded
direct request succeeded. [Metadata](VICTORIA_SAMPLE_METADATA_2026_09_16.json)
records the size, hash, field inventory and aggregate observations; raw incidents
are not included as repository fixtures.

Four records included one Fire, two Other and one Accident / Rescue category.
All had point coordinates and unique incident numbers in this sample. Millisecond
epoch update values matched the corresponding local update strings when converted
to Australia/Melbourne. This is evidence for a time interpretation, not a provider
guarantee. Planned burns, warning polygons, daylight-saving transitions, updates
across multiple snapshots and identifier reuse were not observed.

## Access condition still unresolved

The production [VicEmergency terms](https://emergency.vic.gov.au/about-this-site/terms-of-use)
restrict copying and adaptation of application content and require prior written
permission for broader reuse. They do not establish a developer-feed licence.
The separate [copyright page](https://emergency.vic.gov.au/about-this-site/copyright)
also references applicable terms and third-party restrictions. Generic Victorian
government open-data licensing must not be substituted for this product's terms.

Needed evidence: an EMV developer agreement or official product-specific licence
covering fetching, filtering and display in a distributed Home Assistant integration,
with attribution, polling limits and retention conditions. Commercial Cloud reuse
requires its own scope check. No enquiry was sent and no agreement was accepted.

## Adapter acceptance criteria once access is resolved

1. Validate the `results` envelope and bound bytes, records and nesting. Malformed
   data must not become a successful empty feed.
2. Establish a documented fire-category mapping. Preserve raw categories and count
   excluded or unknown records. Do not turn rescue/accident records into wildfires.
3. Check ID stability across snapshots before relying on `incidentNo` for identity.
4. Verify timestamp semantics, including DST ambiguity and conflicts between epoch
   and local strings. Receipt time must never substitute for event time.
5. Treat coordinates as reported incident locations, not fire extent. Preserve
   source status; `Safe` must not become a general all-clear for a monitored area.
6. Obtain planned-burn examples before supporting that subtype. Do not infer warning
   areas from this incident-point sample or invent thermal observations.
7. Use synthetic fixtures for missing/invalid fields, mixed categories, duplicate
   IDs and date conflicts; add licensed provider fixtures only when permitted.
8. Keep the calendar opt-in, preserve existing identities/history, apply bounded
   requests and stale-data labels, and test local relevance against each monitored
   location rather than always comparing with Home.

This review changes documentation only. Victoria remains a priority, but deployment
depends on the outstanding product-specific conditions and semantic checks above.

## Research continuation after ACT — 2026-09-16 21:06 UTC

Rechecked the official CFA feed page: RSS retains personal/non-commercial and
unmodified-content restrictions, while the separate developer section delegates
access to EMV and lists XML/JSON endpoints. These are distinct products; the RSS
conditions neither grant nor conclusively deny the required developer permission.
Targeted official-site searches did not locate a product-specific developer licence.

A new bounded read of the documented JSON endpoint returned HTTP 200, 1,417 bytes,
application/json; charset=UTF-8, no redirect, HTTP Date 21:06:53 GMT. The root is a
JSON object with a `results` key. This probe establishes availability/envelope only,
not empty-feed semantics, completeness or reuse permission; no raw incidents saved.
Next work is a synthetic envelope/time inspector and verification of EMV developer
conditions before distribution of an operational adapter. ACT uncertainty does not
block that research. WA catalogue also continues to mark incident products as
subject to approval; it is not an unrestricted fallback for Victoria.

## Offline envelope inspector — 2026-09-17

`tools/source_research/victoria_feed.py` now validates the observed `results` array
inside a bounded UTF-8 JSON response. It rejects duplicate keys, non-finite numbers,
malformed/extra envelopes, oversized arrays, nested or empty records and incomplete
responses. Unknown scalar fields and original values are retained without category,
identity, timezone or freshness inference. Empty valid arrays remain distinct from
failures. Diagnostic summaries expose only fixed labels and record counts. It has
no network, persistence or production HA imports. Six synthetic tests bring the
complete offline source suite to 163 passing tests.

A newly located [official support article](https://support.emergency.vic.gov.au/hc/en-gb/articles/235717508-How-do-I-access-the-VicEmergency-data-feed)
says access was not public and invites expressions of interest. It was last updated
6 February 2019, so it cannot establish the current status of the separately listed,
reachable CFA developer endpoint. Its linked EMV emergency-data page returned 403
to the research browser; no access restriction was bypassed. The current CFA page
still lists developer XML/JSON links. These conflicting/dated descriptions leave
product-specific permission unresolved, rather than proving access is prohibited.

Next evidence needed: current EMV developer conditions covering local fetching,
filtering/display, attribution, polling and retention. A request could reference the
exact CFA-listed getIncidentJSON endpoint and distinguish public local HACS use from
any future commercial Cloud product. No enquiry was sent, agreement accepted, live
HA entity created or release published. ACT remains experimental and unchanged.

## Identity and update-time research — 2026-09-17

`victoria_records.py` adds offline inspection of `incidentNo`, `lastUpdatedDt` and
`lastUpdateDateTime`. Candidate IDs retain their exact type/value: integer 1 and
string "1" are not silently merged. Missing, invalid and duplicated identities are
reported; snapshot comparisons reject unusable/duplicate IDs and report overlap
only. Disappearance is not closure and overlap is not lifetime stability.

Update-time inspection explicitly tests the candidate rule: integer Unix epoch
milliseconds versus dd/mm/yyyy HH:MM:SS in Australia/Melbourne using ZoneInfo.
The rule remains unverified provider semantics, even when fields agree. The epoch
candidate is preserved with millisecond precision; comparison uses the second
precision of the local source text. Invalid, missing, conflicting and nonexistent
local clocks have separate outcomes. Fold matches are labelled separately; the
supplied epoch distinguishes the candidate instants without choosing a fold from
local text alone. No current-time, origin-time, host-timezone or yearless-display
fallback is used. Original inputs remain in the evidence object.

Seven synthetic tests cover winter/summer offsets, both autumn-fold instants,
spring gaps, disagreement, millisecond precision, invalid input, typed identities,
duplicates, snapshot changes and redacted summaries. All 170 offline source tests
pass. Production HA imports, data persistence and operational entities remain absent.

Two fresh, bounded HTTPS reads at 08:44:53 and 08:45:55 UTC returned HTTP 200,
8,478 and 9,197 bytes. The first contained 12 records, the second 13. All 25 field
pairs matched the candidate time rule; neither snapshot contained duplicate IDs.
Twelve typed IDs were shared and one appeared only in the second response. Requests
used a 25-second timeout, 1 MiB limit, identity encoding and no redirects; raw data
and IDs stayed in memory. This September sample supports only the observed winter
representation. It proves neither summer/DST-transition behavior, source timestamp
meaning, long-term ID stability nor feed completeness. No source data is a committed
fixture; repository tests use synthetic records only.

## Type and coordinate inspection — 2026-09-17

`victoria_spatial.py` adds offline, exact-field research labels. Fire/Bushfire becomes
a vegetation-fire candidate, Fire/Building a structure-fire report, and Fire/False
Alarm a reported-false-alarm label. Other Fire subtypes remain fire_unspecified;
Medical, Accident / Rescue and Other remain separate. Unknown categories, including
unverified planned-burn feed spellings, remain unknown. No title, agency or status
can override the source category. These labels neither confirm an active wildfire
nor establish a complete provider taxonomy. No records are automatically removed.
Original upstream fields remain in the returned evidence, including test wording.

The [official VicEmergency map legend](https://emergency.vic.gov.au/) explains that
Fire includes vegetation/building fires and alarms, and that an incident icon does
not show fire spread. Planned burns are a separate map category; a map label is not
proof of the developer JSON field combination. The inspector makes no warning-area,
fire-extent, safety or satellite-confirmation inference.

Named latitude/longitude values require finite JSON numbers within global bounds;
booleans and strings are rejected. Missing and incomplete pairs are distinct from
invalid values. There is no swapping, clamping, geocoding or Home fallback. A valid
point does not establish Victorian jurisdiction or positional accuracy; even 0,0
is only numerically valid and is not declared an authentic incident location.

A bounded live read at 08:52:26 UTC returned HTTP 200 and 8,521 bytes, with 12 records:
three Fire/Building, one Fire/Bushfire, one Fire/Other, one Fire/False Alarm, one
Accident / Rescue/Road Accident, four Other/Other and one Medical/Medical. All 12
coordinate pairs were numeric and globally valid. Request limits were 1 MiB and
25 seconds, identity encoding, no redirects. Only category counts and validation
outcomes were retained; no source IDs, medical locations or raw payload fixtures.
This is one observation, not completeness or continued-activity evidence.

Seven new synthetic tests cover category separation, unknowns, unchanged source
text, coordinate bounds, non-finite/boolean/string values, missing pairs and private
aggregate output. All 177 offline tests pass. No production imports, entities,
network polling or history changes are added. Developer permission and real summer/
transition evidence remain unresolved; the provider is still experimental.

## Unified offline report — 2026-09-17

`victoria_report.py` now validates a complete bounded response once and combines
identity, duplicate-ID, update-time, category and coordinate counts. Invalid envelopes
raise before any partial report. Diagnostic output uses fixed labels only: no source
IDs, names, dates, coordinates or unknown-category strings. Dimensions overlap and
must not be added together. Even a valid empty feed keeps production readiness
unestablished and is never an all-clear. Known evidence limitations accompany every
report rather than being inferred away by successful parsing.

Run locally on an already available sample:

```sh
python3 tools/source_research/victoria_report.py /path/to/sample.json
```

Or pass `-` for standard input. The command performs no network requests and writes
no source files. It reads at most 1 MiB plus one detection byte. Invalid/unreadable
input produces a fixed failure object and exit code 2 without raw parser errors,
payload fragments, file paths or partial counts. Success returns exit code 0 and
one JSON report. Retain original upstream data only in an appropriately protected
research workflow; do not commit raw incident samples.

Six new tests exercise mixed findings, duplicate IDs, empty feeds, whole-response
validation, redaction and command success/failure. All 183 source-research tests
pass. No runtime integration, release or HA/history change is included. This report
consolidates existing evidence; it does not close developer-access, summer/DST,
identifier-lifetime, planned-burn taxonomy or feed-completeness questions.

## Two-snapshot offline report — 2026-09-18

The report now accepts `--previous /path/to/earlier.json` alongside the current
sample. Both inputs are bounded and fully validated before output. Typed-ID overlap,
only-before and only-after counts contain no raw identifiers. Invalid/duplicate
identities make comparison unavailable rather than selecting a winner. Caller-supplied
ordering is explicitly unverified; disappearance is never closure and overlap does
not establish lifetime stability. Unreadable or malformed prior input fails the
whole command without leaking its path or returning a partial report.

Five additional tests cover overlapping/empty snapshots, typed IDs, duplicate/missing
identity, per-input limits and actual file/stdin command behavior. All 188 source
research tests pass. There are no network calls, source-file modifications or new
runtime imports. The new [access preflight](PROVIDER_ACCESS_PREFLIGHT.md) applies
before future provider development; Victoria approval is not assumed received.
