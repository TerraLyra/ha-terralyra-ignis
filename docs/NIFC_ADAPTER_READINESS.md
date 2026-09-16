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
