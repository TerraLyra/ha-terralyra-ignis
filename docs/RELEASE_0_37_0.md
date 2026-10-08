# 0.37.0 — Related BM reports beside satellite observations

Prepared for stable publication; not published yet.

## Changes

Opening a satellite marker in the optional IGNIS report-map card can show a
probably related BM OKF report, including its original RSS text, publication time
and source link. Matching uses local settlement identities, conservative Hungarian
wording rules and a six-hour window around satellite observations. No language
model is bundled or downloaded. Multiple possible satellite associations are
explicitly disclosed; the association is not official confirmation.

The popup reads the newest 100 valid reports already in the local archive. Use
the existing BM reports card to retrieve reports first. Opening a marker does
not fetch RSS or article pages. Unmatched/unsupported reports remain unlinked.
The native Home Assistant details button remains available.

The location-summary editor also provides a setup review for entity bindings.

## Upgrade

1. Update through HACS and restart Home Assistant when convenient.
2. Fully reload the browser or Companion App frontend.
3. Keep existing bundled resource URLs and dashboard configuration.
4. Retrieve BM reports using the existing card, then open a Hungarian satellite
   marker in the IGNIS report map. No matching report is a valid empty result.

Satellite coordinates, counts, alerts, manual report links and stored history are
preserved. BM reports do not create satellite fire entities or notifications.

## Validation

The feature PR passed all GitHub checks, including HACS, Hassfest, frontend,
source-research, security and Linux ARM64/x86-64 compatibility checks. Local
validation included 137 BM checks, 32 frontend checks, browser popup checks and
112 targeted HA tests. Production upgrade acceptance remains to be performed.

See [matching limits and usage](BM_SATELLITE_FIRST.md).
