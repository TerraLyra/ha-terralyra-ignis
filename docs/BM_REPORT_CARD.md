# Optional BM OKF report card

Copy `frontend/ignis-bm-reports.js` to `/config/www/ignis-bm-reports.js` and add
`/local/ignis-bm-reports.js?v=1` as a JavaScript module dashboard resource. Add:

```yaml
type: custom:ignis-bm-reports
```

The card currently uses Hungarian labels. Press the retrieval button to request
current RSS notices through `terralyra_ignis.get_official_reports`. There is no
background polling by the card; the existing five-minute shared cache applies.
This needs an integration version containing the fire-scope response enrichment.
On older versions, missing categories remain unknown rather than being discarded.

The default view retains vegetation, mixed and unknown reports. Local-asset
candidates are visible under All reports. The vegetation-only option is stricter
and can miss relevant reports. Labels are experimental text clues, not official
classification or a reliable fire-size filter. Area mentions do not establish
burned acreage. No report is deleted by changing views.

Original RSS descriptions and attributed source links are displayed. No linked
article is fetched. No guessed map coordinates are supplied. The publication
calendar, report archive, satellite data and entity identities are unchanged.
The optional card is a separate frontend asset; HACS does not copy it to www.
