# 0.32.0 — Per-location fire-risk forecasts

## What changes

FRMv3 forecasts can now be enabled separately for monitored locations within the
product's European coverage. Each location has an explicit forecast radius,
independent of satellite monitoring, and its own forecast sensor. Additional
forecasts remain off until configured; no new provider is enabled.

In integration options, open monitored-location management and choose **Location
fire-risk forecast**. Select an enabled covered location, enable its forecast and
enter its radius. Initial retrieval is staggered by roughly 30 seconds to five
minutes; normal refreshes remain roughly twelve hours apart. No data, a provider
failure or an expired UTC product day is not presented as low risk.

The optional summary card now accepts location forecasts using verified location
ID, requested coordinates and forecast radius. A sampled pixel may differ from
the requested point. Wrong bindings suppress the risk rather than showing another
location's forecast. Existing near-home card bindings remain supported.

## Reliability and compatibility

All FRMv3 clients share persistent request pacing and provider cooldowns. Home's
normal polling interval remains unchanged; individual HTTP requests are now spaced
by at least one second. Local storage/cooldown deferrals are distinct from upstream
failures. Initial location requests are staggered and cancelled on unload.

Legacy Home forecast identifiers, radius and map storage are retained. Background
refresh now restores the legacy map cache before fetching. Disabling/deleting a
location does not delete forecast history or stored maps. No history reset or
configuration migration is required.

Offline BM review recognizes additional observed word forms for Söjtör, Pacsa,
Tiszaföldvár and Kunszentmárton, distinguishing responding fire units from incident
mentions. This does not enable automatic BM geolocation.

## Installation

Update through HACS and restart Home Assistant at a suitable time. This release
does not automatically restart HA or edit a dashboard.

To use the new summary binding, replace `/config/www/ignis-location-summary.js`
with the matching release asset and update the existing resource URL's version
query, for example `/local/ignis-location-summary.js?v=0.32.0`. Do not add a duplicate
resource. Other dashboard scripts need no replacement from 0.31.1.

See [summary card configuration](LOCATION_SUMMARY_CARD.md) and
[forecast behavior](LOCATION_FORECAST_IMPLEMENTATION.md). Product dates are UTC;
retrieval time is not model issuance. These are model forecasts, not official
emergency warnings.

## Validation

Implementation CI includes Python/config-flow coverage, localization, platform
compatibility and browser/model checks. Release-candidate CI must pass before
publication. Automated validation is not a claim of live HA acceptance; verify a
current-day result and retained Home entities after installation.
