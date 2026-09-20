# 0.27.0 — optional NIFC official reports

## What is new

US official NIFC / WFIGS / IRWIN reports can be viewed through an optional source
status sensor, timed calendar and map. These are official source reports, separate
from satellite detections, not additional independent fire confirmations or alerts.
Map distances refer to matching monitored locations, not an unrelated Home point.
Wildfire, prescribed-fire and complex records remain distinct.

## Upgrade and first use

1. Make a Home Assistant backup before updating and retain it for rollback.
2. Update TerraLyra IGNIS through HACS and restart Home Assistant.
3. Check that existing locations, entities and sampled history are present.
4. If US reports are wanted, follow [NIFC setup](NIFC_USAGE.md): enable a consumer
   and use the administrator-only `terralyra_ignis.initialize_nifc` action for genuine
   first use. Calendar and map are optional; the map starts off.
5. Check retrieval state and local map/calendar matching. Do not delete storage
   files or reset initialization to bypass a retry pause.

There is no automatic activation of NIFC monitoring. Existing incident identities,
history storage and configuration are not migrated or purged. No Cloud account or
separately installed model package is required.

## Limits and release validation

Requests are bounded and shared, with a persisted minimum 15-minute successful
refresh interval. Partial/oversized responses are rejected. A retained response is
not proof of current fire activity. Calendar timestamps use source update/discovery
fields, not inferred ignition or duration. The map limit is 500 matching records;
over that limit no arbitrary subset is displayed. Report disappearance is not an
all-clear, and the calendar is not a persistent historical archive.

Automated release gates cover HA tests/config-flow coverage, source research,
model packaging, HACS, Hassfest, security and GOES Linux ARM64/x86-64 compatibility.
Passing these checks does not establish live NIFC validation on the user's HA;
that remains the post-installation check. The historical counter discontinuity in
issue #41 is still unresolved and is not claimed fixed by this release.

ACT and Victoria remain offline research only, without production entities or
calendars. Victoria developer permission is pending. Other sources awaiting access
clarification are not included. Optimization remains paused.
