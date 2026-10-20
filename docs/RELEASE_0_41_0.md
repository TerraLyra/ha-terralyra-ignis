# 0.41.0 — Optional INPE Queimadas events

This release brings together INPE state-scoped retrieval, Home Assistant settings,
a returned-event count sensor and an optional map layer. Existing installations
keep INPE disabled until explicitly configured.

## Enable and display

1. Open the integration options and select Configure INPE Queimadas.
2. Enable the source and choose one to three Brazilian state codes.
3. Add an enabled monitored location covering the area of interest, if needed.
4. Turn on the INPE event map switch, then bind it in the IGNIS report map editor.

The sensor shows the number of records returned for the selected states. The map
shows only centroids within enabled monitoring circles, once per source event,
using the nearest matching location as its distance reference. These two counts
can therefore differ. More than 500 matching map records is reported explicitly;
a subset is not silently displayed.

## Data meaning and failure handling

INPE is a provisional, satellite-derived event product. A marker is a representative
centroid, not a fire perimeter. Geometry is based on the previous day; the centroid
list does not provide a verified observation timestamp. Last successful retrieval
is a receipt timestamp, not evidence of current fire activity or complete coverage.
INPE events do not add to satellite incident counts, alerts or independent
corroboration of FIRMS detections. Missing markers do not mean that fires are out.

A valid empty response shows zero returned events. Failed retrieval makes the
sensor unavailable and hides map markers, retaining the previous successful
receipt timestamp. No incident history is deleted. Map visibility changes reuse
the shared inventory without forcing a network request. Retrieval has an hourly
in-memory cooldown with a small random offset; a full HA restart does not retain
that cooldown. No persistent historical INPE archive is added.

Attribution: INPE / Programa Queimadas, CC BY-SA 4.0. The detail card identifies
state/distance filtering, field selection and deduplication as transformations.

## Validation and remaining acceptance

Implementation PRs #225–#229 passed their automated checks. The map implementation
passed all 27 CI checks and 53 frontend unit tests, including INPE visibility and
centroid wording. HA tests cover radius selection, empty/error/recovery transitions,
queued-add cleanup and the marker bound. Full release-candidate CI is required
before publication.

Production INPE setup and map rendering after upgrade remain to be checked.
Automated tests do not establish source uptime, national completeness or freshness
of each event. No live failure injection or production HA changes were performed.

## Update

Update through HACS, restart Home Assistant and fully reload the browser or
Companion App frontend. Existing source settings and dashboard cards are retained.
INPE enablement and map-switch binding are explicit steps after the update.
