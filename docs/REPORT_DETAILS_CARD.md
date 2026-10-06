# Report details map — 0.29.1

> **IGNIS 0.35.0+:** cards are bundled with the integration. See
> [one-time resource setup, updates and older-version migration](CARD_RESOURCES.md).

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

On IGNIS 0.35.0+, register `/terralyra_ignis/cards/ignis-report-map.js` once as a
JavaScript module in Dashboard resources. HACS delivers the matching card file.
When migrating an existing local resource, edit that entry instead of adding a
second one. Keep existing map settings. After updates, restart HA and fully reload
the browser or Companion App frontend; the resource URL stays unchanged.
Older-version installation and rollback are covered in [resource setup](CARD_RESOURCES.md).

### Visual editor (main branch, not yet released)

Add **IGNIS report map** in the dashboard card picker. The visual editor supports
an optional title and explicit Canada/NIFC map-switch bindings. Choose the IGNIS
map visibility switch for the corresponding source, not an unrelated switch.
The list includes switch entities without guessing from their translated names.
No source is enabled and no switch is toggled by making this association.
Unbound or off report controls stay hidden. Missing existing selections remain
visible, so a temporarily unavailable entity does not silently lose its binding.

Existing map entities, zoom and other advanced options are preserved. Edit those
in the code editor. The editor uses Hungarian for a Hungarian HA language and
English otherwise. The initial card makes no automatic report-switch selection.

The binding-status summary distinguishes unbound, invalid, loading, missing,
unavailable, off and on switches. An on switch does not establish fresh reports.
State updates refresh this summary without replacing a title being typed.

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
The model checks cover supported sources, missing descriptions and safe display. The isolated Playwright/Chrome test in
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

## 0.29.1 update

NIFC titles prefer the source incident name, falling back to the entity title.
The integration now provides an actual UTC successful-retrieval timestamp to
NIFC markers. A failed refresh retains that timestamp; restart leaves it unknown
until another successful response. It is not incident start or source update time.
Canada retrieval timestamps are not added by this change. Live NIFC name display
was verified; nonempty incident description display still lacks a live sample.

## Report-source visibility

Configure the actual IGNIS map-control switches explicitly (copy their entity IDs
from HA; the example IDs below are placeholders):

```yaml
report_switches:
  terralyra_ignis_canada_reports: switch.REPLACE_WITH_CANADA_MAP_SWITCH
  terralyra_ignis_nifc_reports: switch.REPLACE_WITH_NIFC_MAP_SWITCH
```

Only an associated switch in state `on` exposes that report-source checkbox.
No report entities are needed: an enabled source with zero matching reports
remains selectable. Off, unknown, unavailable or missing switches hide that
source and suppress its markers. The satellite checkbox remains available.
Checkboxes only filter display and never turn on a provider or call a service.
This binding is required when upgrading older dashboard configurations; without
it report-source controls are hidden. Bind the intended integration's switches
explicitly rather than guessing by translated names or marker availability.


### Description feedback (main branch)

The dialog labels source descriptions explicitly. It distinguishes feeds without
narrative fields, descriptions omitted by the source, fields not requested in a
stored report, and unknown availability. Supplied text remains authoritative even
if an accompanying status is stale. Display truncation at 4,000 characters is
visible; source records are unchanged. No incident-page request is added.
This frontend-only change requires replacing the separately installed card file
and reloading the browser when deployed; it does not require restarting HA.

### Retrieval feedback (main-branch candidate)

Report dialogs translate known Canada and NIFC retrieval states into Hungarian
or English while retaining the original diagnostic code. Known failures and
restored cooldowns show an earlier-report notice. Unknown states stay explicitly
unknown; a success label is accepted only for the corresponding provider.
This does not translate or replace the incident's source status, infer incident
freshness from retrieval success, or infer all-clear from an empty response.
No source retry, persistence, entity identity or history changes are involved.


### Canada receipt timestamp

Canada map records expose the existing coordinator `last_success_at` separately
from source timestamps, matching the dialog's receipt-time field. A failed refresh
retains the previous successful receipt time; an absent receipt remains unknown.
No current clock or source status date is substituted. This attribute requires
an integration update when released, unlike the separately installed card.
