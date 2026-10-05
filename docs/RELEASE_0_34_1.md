# 0.34.1 — Clearer setup errors and report diagnostics

Published stable release.

## Changes

- Location forms retain submitted values after a validation error and explain when
  the alert radius exceeds the monitoring radius. Both radii have guidance in all
  six supported languages. Equal radii remain valid.
- Canada source diagnostics retain the last HTTP error code and completed request
  time across restarts. Skipped requests preserve that evidence; later completed
  requests replace it. Existing review holds, cached reports and request pacing
  remain intact. A legacy hold without a stored code cannot be diagnosed retroactively.
- Sentinel-3A and Sentinel-3B map labels replace internal provider identifiers.
- BM text classification recognizes the reviewed brush-spread and `gyulladt ki`
  constructions. The responder word `tűzoltói` alone no longer acts as fire evidence.
  Actual fire/smoke clues and uncertain wording still prevent a non-fire label.
- Offline BM place review gains explicitly observed Hungarian aliases and an
  area-quantity hint for `hatvan négyzetméteres`. This is research tooling, not
  automatic production geolocation. Original source text is preserved.

## Upgrade

Update through HACS and restart Home Assistant at a suitable time. Existing user
history, location identities, alert radii and notification automations are retained.
No new provider is enabled. The patch does not reset Canada's review hold.

Dashboard JavaScript and the notification blueprint are unchanged from 0.34.0.
If those 0.34.0 resources are already installed, no separate update is needed.
An older summary file still requires the separate 0.34.0 resource update to gain
its visual editor; HACS does not replace dashboard resources or import blueprints.

## Validation

The included feature PRs passed their checks, including 82 offline BM tests for
the latest wording/context change. All 27 candidate checks passed before publication.
Live acceptance of this patch follows installation; no test notification was sent
and no production HA restart was performed during preparation.
