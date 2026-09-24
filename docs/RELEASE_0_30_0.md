# 0.30.0 — Optional BM OKF report list

An optional Hungarian dashboard card displays current BM OKF RSS descriptions,
publication times and original source links. Choose all notices, vegetation-fire
candidates only, or the default vegetation/mixed/unknown view. Retrieval is manual
and uses the existing shared five-minute cache.

Categories are experimental text clues, not official classifications. A vegetation
fire is not necessarily large. Area wording is shown as evidence, never verified
burned acreage. Unknown reports remain visible in the default view. There are no
automatic BM map markers or inferred incident coordinates.

Hungarian GeoNames coverage and evidence-preserving location research are included
for offline evaluation; they do not change runtime nearest-settlement labels.

## Update

Update the integration through HACS and restart Home Assistant. To use the new
optional card, copy the attached `ignis-bm-reports.js` into `/config/www/`, add
`/local/ignis-bm-reports.js?v=0.30.0` as a JavaScript module dashboard resource,
then add a card with `type: custom:ignis-bm-reports`. HACS does not install the
frontend asset automatically. See docs/BM_REPORT_CARD.md.

Existing report calendars, entity identities, user history and monitored locations
are preserved. No new provider or access permission is assumed. Optimization
remains paused. The existing report-map card is unchanged.

## Validation

238 offline research tests and isolated browser checks cover filtering, manual
retrieval, safe rendering, source links, mobile layout and feed failure. Live
Home Assistant installation verification remains a post-update check.
