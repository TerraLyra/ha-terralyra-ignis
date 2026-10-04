# 0.34.0 — Easier setup and clearer satellite source details

Published as a stable release. All 27 candidate checks passed; the merged tree
matched the tested candidate. See [validation status](NEXT_RELEASE_READINESS.md)
for the scope of subsequent live checks.

## Notification blueprint and setup

An optional phone notification blueprint provides short messages in English,
Hungarian, German, Spanish, French and Italian. Select the IGNIS integration,
phone and message language. Setup labels remain English/Hungarian.
The blueprint needs IGNIS 0.33.0+ and HA 2026.9+.

Import the blueprint separately; a HACS update does not install it or replace
existing automations. Before enabling a replacement, check every location's alert
radius and disable the superseded notification automation to avoid duplicate
messages. See [alert setup](ALERT_RADII.md) and the bilingual
[first steps](FIRST_STEPS.md).

## Location summary card

The optional summary card now offers a visual location selector and title field.
Select the intended location explicitly. Existing advanced forecast bindings are
preserved; forecast selection remains explicit.

Update the existing dashboard JavaScript file separately using the matching
`ignis-location-summary.js` asset. Change the existing resource URL's version query
to `?v=0.34.0` and reload the browser; do not register a duplicate resource.
A card-only update does not require a HA restart.

## Probable shared fire markers

Tracks already associated by the existing spatial and temporal rules list their
providers on the shared marker. The label expresses a possible common fire, not
an officially confirmed incident. It follows the HA system language in the six
supported languages, with English fallback.

Entity attributes expose each original track's latest observation timestamp,
coordinates and providers. Historical evidence remains visible without becoming
fresh corroboration. The `current` evidence role means within 30 minutes of the
family's newest observation, not necessarily within 30 minutes of now; the
reference timestamp and window are exposed explicitly. Retrieval time is separate.
The displayed coordinates represent an observation, not a surveyed fire perimeter.

Matching thresholds, alert behavior and incident identities are unchanged. Nearby
markers are not merged merely because they share a settlement name. This release
does not claim that any particular screenshot pair is the same physical fire.

## Upgrade, validation and scope

Update the integration through HACS and restart HA when convenient. Existing
history, monitored locations and provider opt-ins are preserved. No notification
automation is silently rewritten. No new official source is enabled.

Offline BM review gains explicitly reviewed Hungarian settlement/responder forms;
this is research tooling, not automatic production BM geolocation.

All included feature PRs and all 27 candidate checks passed. This release excludes the
still-open location-form guidance (#117) and Canada HTTP diagnostics (#107).
