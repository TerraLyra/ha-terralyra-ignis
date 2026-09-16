# USA NIFC / WFIGS readiness — 2026-09-16

Decision: prioritize current incident points for the first USA official-source
adapter. Keep perimeters as a separate later model extension. Research and offline preparation only; no
runtime adapter, feed activation or claim of complete national coverage.

## Verified primary references

- NIFC WFIGS: https://data-nifc.opendata.arcgis.com/pages/d6ef1367fadc4405b5f09c98e52ed972
- Current locations item: https://www.arcgis.com/home/item.html?id=4181a117dc9e43db8598533e29972015
- Current locations layer: https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/WFIGS_Incident_Locations_Current/FeatureServer/0?f=pjson
- Current perimeters metadata: https://www.arcgis.com/sharing/rest/content/items/d1c32af3212341869b3c810f1a215824/info/metadata/metadata.xml?format=default&output=html

## Layer observations

The locations layer identifies its item ID as 4181a117dc9e43db8598533e29972015.
It is a point view, with WF/Wildfire, RX/Prescribed Fire and CX/Incident Complex
categories. Date-field metadata explicitly uses UTC. Native spatial reference is
WKID 4269; do not silently label native coordinates as WGS84. JSON/GeoJSON queries,
ordering and pagination are supported; maxRecordCount is 2,000. These are dated
metadata observations, not fixed future guarantees.

Its view definition applies ActiveFireCandidate, discovery-date and size-dependent
modification-time cutoffs. Disappearance from this view is not a closure event.
Preserve retained history; no purge or automatic closure based on absence.

## Proposed implementation contract

- Keep WF, RX and CX separate. A complex and its members must not be assumed to be
  independent fires; defer matching to a separately justified relationship model.
- Request an explicit output coordinate system and validate returned metadata.
- Bound response size, pages and records. Detect partial/transfer-limit responses;
  do not report incomplete pages as a complete successful snapshot.
- Establish stable incident identity from documented fields, not an assumed durable
  OBJECTID. Check duplicate/conflicting IDs and source updates across snapshots.
- Distinguish discovery, modification, containment/control/out and retrieval dates.
- Preserve source attribution and source-specific status. No synthetic thermal data.
- Start with incident points. Fire perimeters require an incident-area role rather
  than reusing warning-area geometry. Missing perimeters are not missing fires.
- No user-location transmission until the fetch/filter design explicitly accounts
  for it; statewide/national retrieval and local filtering need boundedness review.

## Open evidence

The initial reader could not display product terms. The subsequent official item
overview review below supersedes that access limitation. Request-rate guidance,
identity behavior across snapshots and a bounded retrieval policy still need work.

Australia remains the first regional priority. ACT now waits for provider semantics
and a vegetation-fire example; Victoria/WA retain their access/terms gates. USA
research can proceed independently. This is an engineering sequence, not an annual
wildfire-severity ranking; the worldwide quantitative country screen remains undone.

## Direct bounded query follow-up

A five-record query returned HTTP 200, 2,260 bytes, four RX records and one WF.
Requested fields: OBJECTID, IrwinID, IncidentTypeCategory, FireDiscoveryDateTime,
ModifiedOnDateTime_dt; ordered by OBJECTID ASC, outSR=4326. Returned geometry metadata
confirmed WKID 4326. Date values were integers; IRWIN IDs were distinct in this sample.
The response explicitly set exceededTransferLimit=true: this is a partial page,
not five total incidents. No additional pages were fetched. The raw sample and internal aggregate metadata are not distributed in this repo.

This verifies basic anonymous query access, category separation and partial-page
signalling. It does not prove stable IDs, source freshness, complete pagination or
every reuse condition. The later product overview review below supplies direct
publisher evidence; third-party public-domain claims are not relied upon.

The official EGP data page (https://portal.wildfire.gov/egp/data/) describes its data
as primarily public domain, while noting dataset-specific access controls. This is
useful publisher-level evidence but does not establish every condition for the
specific WFIGS item. The application's Esri licence is distinct from dataset rights.


## Product overview verified — 2026-09-16

The official item overview was read directly in the browser. It identifies NIFC as
owner and marks the item authoritative. Its Terms of use are a disclaimer covering
accuracy, completeness, changing data, geospatial limitations and user responsibility.
No explicit fee, account requirement or noncommercial restriction was displayed in
those terms. This is not an explicit CC licence grant or a legal guarantee of all
uses; the general EGP public-domain statement must retain its qualification.

Retain attribution to NIFC / WFIGS / IRWIN and a link to the original item. The
acknowledgments include DOI Office of Wildland Fire / IRWIN, USDA Forest Service,
NPS, FWS, BIA, BLM, NASF, USFA and NWCG. These observations support further public,
read-only adapter preparation; they do not authorize a paid redistribution service.

The overview documents a five-minute IRWIN refresh and hourly fall-off filtering:
under 10 acres after three days without updates, 10–100 after eight days, over 100
after fourteen days. Other validity, incident-type, date and status filters apply.
Disappearance therefore must never be interpreted as closure or history deletion.
This upstream refresh cadence is not a published client request-rate allowance.

Verified field meanings:
- IrwinID identifies an IRWIN incident record; OBJECTID is paging metadata.
- FireDiscoveryDateTime is reported discovery/confirmation, not guaranteed ignition.
- ModifiedOnDateTime_dt is IRWIN record modification, not observation or receipt.
- CreatedOnDateTime_dt is record creation, not fire discovery.
- ContainmentDateTime, ControlDateTime and FireOutDateTime have separate meanings.
- CpxID identifies the parent complex; IsCpxChild indicates membership.

The offline normalizer preserves missing dates/geometry, converts integer UTC epoch
milliseconds without a machine-time fallback, and rejects duplicate IRWIN IDs and
unknown categories. It does not resolve complexes, assess freshness, fetch pages,
close incidents, write history or activate HA entities. UUID syntax acceptance is a
narrow implementation contract supported by the sample, not a claim that all future
IRWIN identifiers must retain this representation.

Validation: 66 synthetic offline tests passed locally, including nine new record
normalization tests. No live feed request or HA operation is performed by these tests.

## Bounded research retrieval follow-up

An opt-in standard-library research fetcher now connects envelope validation and
record normalization, with fixed query provenance and byte/page/record budgets.
It rejects unknown continuation, service/transport errors and cross-page identity
conflicts without returning partial records. This remains outside HA runtime.
There was no live multi-page crawl in this step. All 76 offline tests passed.

Before runtime integration: implement a cancellable overall network deadline and
request-rate/backoff policy, validate live multi-page behavior, model complex/member
relationships, and decide freshness and opt-in UI behavior. Pagination termination
still does not establish a consistent snapshot or authorize history reconciliation.

## Asynchronous deadline follow-up

The research-only asynchronous entry point now bounds the whole network operation
with a 60-second default deadline and supports external cancellation. It shares the
same validation and limit implementation as the synchronous fetcher. Automatic
retries are explicitly disabled, including for rate limits and server errors.
The production scheduling/cooldown policy and live transport verification remain
open. Synchronous validation is byte-bounded but not preemptible. No HA configuration,
release, history write or live source request was performed. All 81 offline tests pass.

## Live bounded transport verification — 2026-09-16

Using Python 3.13 and aiohttp 3.14.3 in an isolated temporary environment, the actual
async HTTP transport fetched two pages at offsets 0 and 5, five records each.
Each response was 2,260 bytes and explicitly reported further results. Both passed
page, record and cross-page identity checks. The operation then raised the expected
record-budget exhaustion error without returning a successful result. This verifies
two-page interoperability and fail-closed limits, NOT a complete national snapshot
or a successful terminal-page run. No raw incident payload was saved or published.

Synthetic transport tests additionally cover streamed byte overflow, refused
redirects/429/503/compression, and response cleanup after cancellation. The complete
85-test offline suite passed on local Python 3.9 and 3.13. Production activation,
automatic retry scheduling and full snapshot consistency remain out of scope.

## Refresh policy prototype — 2026-09-16

Pure, offline-testable refresh state transitions now specify a 15-minute normal
interval and capped exponential waits for transient errors. Server Retry-After and
existing longer cooldowns are respected. Invalid data/access denial stop automatic
eligibility until review. Failures preserve the last successful response and receipt
time. These are proposed client defaults, not a provider-authorized request rate.
No scheduler or HA adapter uses this policy yet. Monotonic clock deadlines are
process-local; persistent cooldown recovery and atomic in-flight coordination remain
runtime integration requirements. An empty response never instructs history deletion.

## Coordinator prototype

An explicit, disabled-by-default research coordinator connects fetches and refresh
policy, excludes concurrent requests within one instance/event loop, and retains the
last response on known failures. Cooldown-only checkpoint export/restore survives a
new monotonic-clock origin by conservatively restarting the saved remaining wait.
There is still no durable storage adapter, HA scheduling or actual restart test with
persisted state. History is not read or written. 103 offline tests pass.

## Cooldown storage follow-up

An explicit dedicated-file storage helper now atomically replaces validated cooldown
metadata and rejects missing/corrupt/oversized files without resetting eligibility.
A separate-process test verified restoration with a new monotonic-clock origin.
Synthetic disk replacement failure preserved the prior checkpoint and an unrelated
history file. 109 tests passed on Python 3.9 and 3.13. No actual HA history was touched.
Coordinator lifecycle wiring, storage-failure handling, cross-process coordination and
power-loss durability remain unimplemented. No automatic startup or HA activation.

## Persistent lifecycle prototype

The persistent wrapper now loads before eligibility, saves a pause marker before
network access, and saves final policy state after completion. Cancellation or a
final save failure leaves manual review required after restart; a preflight save
failure prevents the request. Previous in-memory response data is retained on storage
failure. 116 synthetic tests pass. Remaining runtime work includes nonblocking HA
storage integration, one-owner enforcement, user-facing diagnostics/recovery and
source freshness/complex semantics. No live HA configuration or history was changed.

## Async storage interface and diagnostics prototype

The existing integration uses async_load/async_save store interfaces. A separate
research coordinator now accepts that interface, awaits writes and preserves request
ownership until a cancelled save settles. Fixed diagnostics identify load/save
failures without raw errors or paths. 121 offline tests pass. Actual HA Store wiring,
translated Repairs, manual recovery and hung-storage handling remain outstanding;
this is not a deployed HA adapter and performs no actual HA storage operations.

## Translated repair helper preparation

A currently uncalled HA repair helper maps fixed NIFC diagnostic codes to English
and Hungarian messages for load/save errors, manual review, unexpected data and
access denial. No automatic reset or fix flow is offered. Unknown/transitional
statuses do not clear existing actionable issues; explicit recovery or disablement
clears only the issue scoped to that entry. Transient outages remain diagnostics.
Real issue-registry tests cover mapping, translations, entry isolation and clearing.
No runtime caller, NIFC option, source activation or history operation is added.

## Combined storage/diagnostic lifecycle tests

Test-only wiring now synchronizes prototype diagnostics into the real HA issue
registry while using the actual HA Store API with isolated pytest storage. Scenarios
cover preflight save failure preventing any fetch, missing state followed by explicit
synthetic recovery, preservation of another entry's issue, and cancelled requests
remaining paused after reload. Production setup still has no NIFC runtime caller;
the synthetic recovery is not an implemented user-facing reset action.
