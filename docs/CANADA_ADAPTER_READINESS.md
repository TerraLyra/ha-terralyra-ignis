# Canada CWFIF readiness — 2026-09-21

Status: experimental integration-owned client; no registered HA provider or calendar.

## Access evidence

The current [Active Wildfires in Canada catalogue entry](https://cwfis.cfs.nrcan.gc.ca/en/catalogue/results/bd641635-d30d-4b77-abc0-d6b59b1e8a00)
explicitly assigns Open Government Licence - Canada to the product and links the
new `public:cwfif_national_activefires` layer. Separate bespoke approval is not
indicated for attributed HACS use. The [licence](https://open.canada.ca/en/open-government-licence-canada)
permits adaptation and redistribution, including commercial use, subject to its
attribution, exceptions and non-endorsement conditions. It is not an API quota.

An older 2020 metadata PDF also mentions an end-user agreement, whose linked URL
returns 404. That failure alone proves nothing about permission; the current
product-specific licence is the basis of the access assessment.
The [downloads licence notice](https://cwfis.cfs.nrcan.gc.ca/downloads/licence.txt)
specifies Canadian Forest Service / CWFIS / NRCan attribution. Preserve that
source identification and the licence link in future presentation.

## Observed data behavior

A bounded sample returned 382 of 382 reported matches with unique national IDs;
all point coordinates were finite and within geographic bounds. Some records
refer to earlier fire years. Do not drop those solely for their year or infer
fresh incident confirmation from a recent record-validity time.

Three matched records had changed GeoJSON feature IDs between requests despite
unchanged national and numeric record IDs. Use national fire ID and agency for
incident identity; transport IDs are unsuitable. Long-term reuse behavior has
not been exhaustively demonstrated.

All four date fields in the full sample and six winter/summer sample records
carried explicit UTC offsets. Missing or naive dates are rejected rather than
interpreted. `situation_report_date` can mean initial receipt, not ignition.
Current record selection uses half-open validity: start <= now < end.
All 382 sampled records used containment -1, which must remain unknown.

## Implemented research checks

The isolated client and synthetic tests cover bounded downloads, total network
deadline, partial responses, identities, coordinates, separate source timestamps,
retry pauses, cancellation, single-owner concurrency and persistent reservations.
The presentation preserves malformed/unknown optional status metadata with explicit
warnings; containment outside 0–100 is unknown. Multiple enabled monitored places
are matched independently with a deterministic nearest-place distance reference,
without a Home fallback. Removing or disabling a place removes its presentation
match without changing the source record.

The canonical client now lives in `official_sources/canada`; standalone research
entry points load the same modules. Import and construction perform no I/O.
HA package identity is covered separately in the full integration test suite.

An isolated lifecycle adapter now shares one task across eligible consumers, is
disabled by default, cancels when its last consumer leaves, and waits for
cancellation cleanup on shutdown. Restart honors the persisted request pause.
Repeated shutdown does not re-cancel a pending durable write. This adapter is
not registered with Home Assistant; HA event/timer/storage integration remains
a production gate.

No source raw samples or private monitored locations are committed.

## Remaining production gates

- HA presentation distinct from satellite observations; research radius matching
  and conservative status labels now have synthetic coverage.
- Unknown/new category handling and metadata warnings without false certainty.
- HA lifecycle, storage ownership and post-restart behavior in integration tests.
- Attribution/UI review; no unsupported emergency-warning or all-clear claims.
- Request cadence remains a conservative design choice, not an upstream guarantee.
- Review the complete change before enabling any real HA entity or publishing it.

The user has added a Canadian monitored point for later validation. No point
coordinates were sent upstream in this research. Optimization remains paused.

## HA persistence boundary — 2026-09-22

A lazy HA owner now supplies the shared HA HTTP session and a dedicated
`terralyra_ignis.canada_state` Store to the existing controller. The owner is not
registered or invoked by setup. The adapter requires explicit first-use
initialization; missing or corrupt data cannot silently reset the request pause.
Existing valid state is adopted without replacement. Storage errors latch a block
for the owner lifetime. Cancellation waits for a controller-owned save before
releasing its lock. Research file storage and HA storage share the same codec.

HA storage waits are bounded to 30 seconds. Timed-out operations remain owned
and HA-tracked until completion; no overlapping write or new request is allowed.
Late failure is retrieved and the review block remains even after late success.

Synthetic storage tests cover restart, corruption, failed reservation writes and
cancellation during persistence. HA tests cover lazy ownership and real Store
roundtrip. An administrator-facing initialization/recovery flow, scheduler and source-status entity remain outstanding before
activation. No history migration or removal is performed.

## Administrator preparation and recovery

`initialize_canada` and `recover_canada` require an identified administrator,
a loaded IGNIS entry and an explicit confirmation. Registration performs no I/O.
Initialization preserves existing state. Recovery refuses pending storage work,
missing/corrupt data or a missing cooldown. It preserves cached reports and adds
at least one hour without shortening a longer server wait. Neither action enables
retrieval. Canada remains without runtime scheduling or entities.

## Opt-in diagnostic runtime

The Canada source-status diagnostic sensor is registered disabled by default.
An enabled sensor attaches to a single HA runtime shared by config entries.
The one-minute timer only checks eligibility; persisted request pauses remain
owned by the controller. No enabled monitored place means no request. Missing
first-use storage is surfaced as initialization_required without creating it.
The admin initialization action wakes an already enabled runtime. Last-consumer
unload and HA shutdown cancel retrieval and remove the timer.

This step exposes retrieval health only, not an active-fire count or warning.
Canada map/calendar entities and release validation are still outstanding.

## Official map and calendar presentation

Canada now has a separate opt-in map switch and disabled-by-default official
reports calendar. Map coordinates come from validated upstream Points; distances
refer to the nearest matching enabled monitored location, never an unrelated Home.
IDs derive from agency and national fire ID, not changing transport feature IDs.
More than 500 relevant reports raises a display-limit status rather than silently
showing a subset. Removing display entities does not edit source/history storage.

Calendar markers use status_date with its explicit offset. A one-second marker is
not fire duration or ignition; record validity and situation timestamps remain
separately described. Retained responses are identified. Attribution, catalogue
and licence links are included. Final release validation and live opt-in checks
are still required; no release is published by this change.
