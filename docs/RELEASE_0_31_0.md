# 0.31.0 — Location summary and source-aware map controls

Release candidate; publication and installation are not yet complete.

## User-visible changes

The optional location summary card shows tracked satellite incident counts and
source health for one explicitly selected monitored location. Its nearest-distance
line uses only current active incidents inside that location's radius, never a
global Home distance or historical minimum. Missing data remains missing, not zero.
Partial retrieval keeps snapshot semantics and its visible limitation.

An optional, verified near-home FRMv3 binding adds the current UTC product-day risk,
validity and receipt age. This is not an all-location forecast: the existing
provider fetches for HA home only. Model issuance is not inferred from receipt time.
Unavailable, expired, ambiguous or mismatched data cannot produce a current risk.
Official restrictions remain unconnected and are not presented as “no restriction”.

Canada/NIFC report-map controls follow explicit map-switch associations. Disabled,
missing or unavailable switches hide their controls and markers; an enabled source
with zero reports remains selectable. Satellite observations remain separate.

Offline research includes reviewed Hungarian place forms/context and bounded
France/Spain tooling. These do not enable new production providers or BM markers.

## Updating an existing installation

1. Update IGNIS through HACS and restart HA for the new location-distance attribute.
2. If using the optional summary, replace `/config/www/ignis-location-summary.js`
   with `frontend/ignis-location-summary.js` from this version. Change the existing
   JavaScript module resource query to `?v=0.31.0` and reload the browser.
3. If using the optional report map, replace its existing local JS file with
   `frontend/ignis-report-map.js`. Preserve a custom filename such as
   `ignis-report-map-v2.js`; update that existing resource query to `?v=0.31.0`.
   Add the explicit `report_switches` mapping documented in
   [report map setup](REPORT_DETAILS_CARD.md), or Canada/NIFC controls stay hidden.
4. Preserve existing card settings. Summary setup and optional forecast binding
   are documented in [location summary](LOCATION_SUMMARY_CARD.md). Do not copy
   example coordinates; verify the actual monitored location against HA home.

HACS does not copy these separate dashboard resources into `/config/www`.
Keep one resource registration per card, and retain a copy of the previous JS
before replacement. The BM card resource does not need replacement for this update.
No entity removal, Recorder purge, storage reset or new account is required.

## Validation scope

Feature PRs #75–77 and #80 passed their CI checks. Local frontend model and isolated
Chrome tests cover identity mismatch, current versus stale values, safe text,
unavailability and mobile layout. PR #80's HA regression verifies exact-location
nearest-distance selection, lifecycle/radius exclusions and zero versus missing.
Live summary/forecast/map smoke checks were performed separately; the new backend
distance attribute still needs a post-installation check. No continuous uptime or
complete historical equivalence is claimed. Candidate CI must pass before release.
