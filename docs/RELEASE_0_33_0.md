# 0.33.0 — Separate monitoring and satellite alert radii

Each enabled monitored location now has a monitoring radius and an equal or smaller
satellite alert radius. Monitoring continues to control observation coverage;
notifications can use the dedicated `terralyra_ignis_fire_alert` event.

The event evaluates every location independently and includes all qualifying
locations in `alert_locations`. It covers new incidents inside an alert area and
newer observations entering it. The boundary is included. Startup and location
configuration changes establish a quiet baseline. Remaining inside, corroborating
satellite tracks, stale observations and temporary missing/inactive snapshots do
not repeat an existing alert. A newer outside observation followed by a newer
inside observation can alert again.

## Upgrade and notification migration

Update through HACS and restart Home Assistant at a suitable time. Existing
location records without an explicit alert radius use their monitoring radius.
Existing history and location identities are preserved.

**Existing notification automations do not switch to the new radius automatically.**
Before replacing a state-change or `terralyra_ignis_new_fire` trigger, set the alert
radius for each location to preserve the actual previous notification threshold.
Then use the new alert event and disable the replaced notification trigger to
avoid duplicate messages. See [alert setup](ALERT_RADII.md) for an example.

Old observation and trend events retain their behavior. Official reports do not
emit the new satellite alert event. Fire-risk forecast radii remain independent.

## Map and optional location summary

The monitoring-area source shows an outer monitoring circle and, when smaller,
an inner alert circle. Equal radii produce one circle. The optional location
summary displays both values.

If the optional summary card is installed, replace its existing file with the
matching `ignis-location-summary.js` asset, update the existing resource URL's
version query to `?v=0.33.0`, and reload the browser. Do not register a duplicate
resource. A card-only update does not require a Home Assistant restart.

## Validation and scope

The feature passed 1172 Home Assistant tests, 100% config-flow coverage and all
27 feature-PR checks. Release-candidate checks must also pass before publication.
Coverage includes event delivery, independent overlapping locations, boundary
entry, restart/configuration baselines, stale/missing data and circle geometry.
Live acceptance follows installation; it has not been claimed by offline tests.

Alert transition memory is bounded to 10,000 track/location pairs. Evicted
identities can subsequently be treated as new. This memory is separate from user
history. No new provider is enabled and no existing external automation is rewritten.
