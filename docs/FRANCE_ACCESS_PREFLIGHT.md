# France: FR-Alert offline research — 2026-09-25

## Current decision — 2026-09-28

Offline research only. No production provider, scheduled retrieval, HA entities
or release changes. The technical enquiry was submitted on September 28; reply
is pending. A supported retrieval contract, lifecycle relationships and reliable
timestamp/geometry semantics remain unresolved. Explicit exercises are marked
but retained; other records are not automatically classified as active fires.
The entries below are chronological research notes; later findings supersede
earlier implementation descriptions and enquiry status.

Official terms: https://fr-alert.gouv.fr/mentions-legales
Site content is under Etalab 2.0 except explicitly identified third-party rights.
Preserve source, last-update date and non-misleading presentation. No blanket
permission enquiry is needed for covered content. A supported bounded feed,
polling policy and publication delay remain unverified.

Sample: https://www.fr-alert.gouv.fr/les-alertes/FR-ALERT.1786010946.90000.0
One 25,061-byte detail page was retrieved. Embedded drupal-settings-json contains
alert_entity.infos, original headline/description/sender, epoch-like values,
Europe/Paris timezone and warning area polygons. This is a website implementation
format, not an established public API contract. The URL number is not assumed
to be the event time or a stable incident identifier.

Interpreting effective/onset as Unix seconds gives 2026-07-31 19:15:30 +02:00;
expires gives 2026-08-02 19:15:30 +02:00. Both match displayed dates/minutes.
This is one summer sample, not proof for winter, overseas zones, DST transitions
or all timestamp fields. Created/updated are kept distinct from event time.
No active/expired/cancelled status is inferred from state or from the page title.

The geography_center lat/lon fields appear reversed relative to the area's
polygon (lat about 6.15, lon about 43.46 versus polygon latitude about 43.46).
Do not silently swap, plot this centre, or use any warning-area centre as an
ignition point. Preserve geometry verbatim pending validation of each encoding.

fr_alert_review.py reads local HTML only (1 MiB / 20 info-object limits), extracts
one complete settings block, preserves each info object including unknown fields
and original description markup, and emits explicitly unverified epoch candidates.
No HTML is rendered or executed. is_test and active remain unknown; absence of
an explicit verified test field must not be treated as actual-event evidence.
Tests cover size, malformed/missing/duplicate blocks, timestamps and preservation.
281 offline research tests pass. No production provider or HA entity is added.

Next evidence: an explicit exercise record, update/cancellation relationships,
a winter or overseas example, and a supported incremental/list endpoint. Full
archive HTML exceeded 4 MiB during earlier bounded inspection and is not a
suitable per-installation polling design. No request has been sent to FR-Alert.

## Explicit exercise evidence

https://www.fr-alert.gouv.fr/les-alertes/FR-ALERT.1782917873.90000.0
The 22,332-byte Saint-Martin/Marigot detail contains level=EXERCISE, an explicit
exercise headline and a technical-test description stating no action required.
The archive list also labels this record Exercice. The inspector now reports
is_test=true with field-specific evidence for exact EXERCISE only, retaining
all original content. Unknown/missing levels remain unknown, not false. TEST
is not mapped until a real payload verifies that spelling in the level field.
This is classification only; the inspector does not remove records.

The sample uses America/Martinique, demonstrating why Europe/Paris cannot be
applied globally to this French source. Timestamp conversion still requires
sample-specific display checks. The public alert_entity_service.js explicitly
parses polygon pairs as latitude,longitude before passing longitude,latitude to
OpenLayers, corroborating polygon order independently of geography_center.
The script exposes map utilities and icon fetching, not a verified incremental
alert API. Cancellation/update semantics and winter evidence remain open.

## Winter and chronology evidence

https://www.fr-alert.gouv.fr/les-alertes/FR-ALERT.1769635168.90000.0
A 21,954-byte January exercise detail matches epoch-seconds interpretation at
Europe/Paris UTC+1: effective/onset 2026-01-28 21:19:28; expires 17:17:44 the
same day. The website itself displays these conflicting times. Preserve them;
do not correct the expiry or infer that this represents a cancellation.
The inspector flags expires_before_effective/onset and keeps active unknown.

Local-time candidates now use the supplied IANA zone through zoneinfo, without
fallback to Paris or fixed offsets. Regression cases cover winter/summer, both
sides of spring transition, both repeated autumn hours and America/Martinique.
DST cases are synthetic validation of conversion, not real upstream DST samples.
286 offline tests pass. Timestamp semantics remain explicitly unverified overall.

The public alert_page.js reads embedded infos and draws areas locally; it does
not establish an incremental alert endpoint. It parses polygon pairs as lat,lon.
Its circle conversion is not a sufficient radius-unit specification. Supported
bounded discovery and update/cancellation relationships remain open; there is
still no production adapter or recurring retrieval.

## Homepage discovery sample

https://www.fr-alert.gouv.fr/ returned approximately 512 KiB with an embedded
alert_entity.alerts collection of 126 records. Status counts: Actual 67,
Exercice 59. All msg_type values were Alert and all reference values null.
This does not establish absence of updates/cancellations in the service, nor
that the homepage is complete/current. Actual is not equivalent to active.

fr_alert_listing.py inspects saved HTML only, bounded to 1 MiB and 200 alerts.
It preserves entire source records including status, message type, references
and nested infos, labels exact Exercice as test, retains duplicate IDs with an
issue and never infers completeness from an empty result. Replaying the sample
returns all 126 rows including all 59 exercises. All 291 research tests pass.

Homepage nested info timezone has a different shape from detail pages: an object
with a numeric-string key and a translate label, rather than a single-item list.
The listing inspector preserves this verbatim; it does not pass this structure
into the detail timestamp interpreter or substitute a timezone. A shared future
adapter must validate both shapes explicitly. No supported incremental endpoint
or polling interval has yet been verified. Homepage reuse remains offline only.

## Shared detail/list review — 2026-09-28

The homepage now passes nested infos through the same bounded offline reviewer
as detail pages. Timezone handling accepts the observed singleton list and the
observed object containing key "0" plus optional display-only "translate".
Extra indexed entries are rejected as ambiguous; the translation label is never
used as an IANA zone. Invalid/missing infos retain the parent source record and
add an issue, without treating absence as an empty successful result.

Replay of the saved September 25 homepage preserved 126 alerts and 126 infos;
all 126 produced local-time candidates and none had an invalid timezone. This
is a replay, not a fresh retrieval or proof of correct source semantics.
Regression checks cover equivalent encodings, ambiguous zones and malformed
nested infos. All 294 offline research tests pass. Runtime eligibility and
snapshot completeness remain false; active state remains unknown.

## Offline snapshot comparison — 2026-09-28

The official /modules/custom/alert_entity/js/alert_block.js reads the embedded
alerts collection. No incremental retrieval contract was found in that script.
It constructs JavaScript Date from effective * 1000, supporting the seconds
interpretation, but browser-local formatting means map popup text is not a
reliable independent timezone oracle. It passes geography_center's lat/lon
fields in reversed field-name order to fromLonLat, then adds a random projected
offset (up to 50 units per axis). Do not derive incident coordinates from visible
markers, or copy the jitter into source data.

fr_alert_changes.py compares two bounded saved homepage samples. It distinguishes
newly observed, changed, unchanged, missing-from-second-sample and duplicate-ID
ambiguity, retaining both source versions. Missing identity is reported by row
index. This is document comparison, not incident lifecycle resolution; no
cancellation or extinction follows from disappearance. Failed input raises an
error rather than becoming an empty snapshot. Six regressions pass; the full
suite passes 300 tests. No scheduled fetch or runtime entity was added.

## Fresh comparison and technical enquiry route — 2026-09-28

One new homepage retrieval stayed below 1 MiB. Comparison against the saved
September 25 sample yielded 126 unchanged source records. This verifies the
unchanged-data path on real samples; changed/cancelled records are still only
covered synthetically. It does not prove freshness or completeness.

Official contact route verified through the FR-Alert FAQ and contact page:
https://www.fr-alert.gouv.fr/nous-contacter
https://fr-alert.gouv.fr/foire-aux-questions
No enquiry sent. Ask for supported machine access and publication latency,
coverage/retention of homepage versus archive, update/cancellation references,
and recommended per-installation polling. Existing Etalab terms are not being
replaced with an unnecessary blanket permission request.

## Enquiry submitted — 2026-09-28

The user confirmed submitting the prepared technical enquiry through the official
FR-Alert contact form using the in-app browser. Response pending. This supersedes
earlier unsent-status notes; do not send a duplicate. Questions cover supported
machine access, homepage completeness/publication delay, update/cancellation
relationships and recommended per-installation polling. Submission is not a
technical confirmation or approval. Offline research remains separate from HA.
