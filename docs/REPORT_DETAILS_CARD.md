# Report details map — 0.29.0

This optional dashboard resource wraps Home Assistant's existing map card. It
intercepts report clicks only inside this card, for the Canada and NIFC sources.
Satellite markers, monitoring areas and other entities retain HA's normal dialog.
It neither patches HA globally nor changes entity IDs, history or source fetching.

The modal shows existing attributed structured fields. NIFC now requests the official IncidentName (50 characters) and
IncidentShortDescription (80 characters) fields. These are source strings, not
a generated article. Missing fields (older installations), empty descriptions
and supplied descriptions are distinguished. Canada is explicitly labelled `not_in_feed`: its WFS DescribeFeatureType schema
checked on 2026-09-22 contains no narrative description field. This claim is
limited to this feed, not all Canadian agency products. The source link opens the source catalogue, not a
fabricated incident-specific URL. Missing timestamps stay missing; HA state-change
time is never presented as publication or retrieval time. Unknown control codes
remain the original source values. Text is rendered as text, never upstream HTML.

## Installation and updates

The JavaScript card is distributed separately from the HACS integration.
Download it from the 0.29.0 release assets. It is not installed automatically.
Copy `frontend/ignis-report-map.js` to `/config/www/ignis-report-map.js` and register
`/local/ignis-report-map.js` as a JavaScript module in Dashboard resources.
For an update, replace the card file, change its resource URL query to
`?v=0.29.0`, and reload the browser. Keep only one resource entry for this card.
If you already use a differently named card file, update that file or point the
existing resource entry to the new one. A browser reload is required because
an already registered custom element cannot be replaced in the current page.

On a duplicate card, retain all existing map settings and change only:

```yaml
type: custom:ignis-report-map
geo_location_sources:
  - terralyra_ignis
  - terralyra_ignis_canada_reports
  - terralyra_ignis_nifc_reports
```

The normal map settings remain available through YAML. Returning `type` to `map`
restores the standard card without touching entities or recorded history.
English and Hungarian labels are provided; other languages use English.

## Validation and remaining work

Run `node --test tests/frontend/report-map.test.mjs`.
The six model checks pass. The isolated Playwright/Chrome test in
`tests/frontend/report-map-browser.cjs` also passes: HTML is inert text, unsafe
links are absent, supported report clicks are scoped to this card, ordinary
entity clicks and the HA-details button propagate normally, the modal fits a
390px viewport, removed reports are explicit, and Escape closes the modal.
This test uses a stub map element; it is not a real HA compatibility test.
Before release, validate the nested HA map and click forwarding in the installed
HA frontend on desktop and mobile. Check keyboard close/focus, source failures,
entity removal while open, multiple cards and unchanged satellite dialogs.
The layer switches and age filter were verified on live HA: Canada markers
58 -> 0 when disabled and 58 -> 16 with the seven-day filter; 46 satellite
markers remained. The user confirmed the earlier report dialog. Updated NIFC
text retrieval still requires post-upgrade live validation.

Calendar-only BM OKF, NSW RFS, Queensland and GDACS reports are not automatically
map entities. Their text adapters and a shared report contract remain necessary;
do not create coordinates merely to make a report fit a map.

BM OKF location extraction is the next separate stage: retain original evidence,
return review-only settlement candidates with ambiguity and approximation labels,
and never turn a settlement centre into an exact incident coordinate. Event-page
coordinate collection remains gated on source-use clarification.

## Layer controls and age filter

Three local controls independently show satellite observations, Canada reports
and NIFC reports. The card includes these sources automatically; other map
settings are preserved. A filter allows all, 1, 7 or 30 days since the official
status/update timestamp. It never uses record validity or HA last_changed as
report age. Unknown, timezone-less and future timestamps remain visible and are
labelled uncertain. Filters are per-card session settings and do not delete
entities, source responses or Recorder history. Other HA consumers are unaffected.

NIFC field schema checked 2026-09-22:
https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/WFIGS_Incident_Locations_Current/FeatureServer/0?f=pjson

The new backend text fields require an integration update; copying only the JS
file cannot make a 0.28.0 installation retrieve text. No webpage scraping added.
