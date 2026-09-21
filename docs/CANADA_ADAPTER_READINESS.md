# Canada CWFIF readiness — 2026-09-21

Status: experimental research client; no production HA provider or calendar.

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
