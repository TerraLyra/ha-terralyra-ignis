# Optional BM OKF report card

> **IGNIS 0.35.0+:** cards are bundled with the integration. See
> [one-time resource setup, updates and older-version migration](CARD_RESOURCES.md).

On IGNIS 0.35.0+, add `/terralyra_ignis/cards/ignis-bm-reports.js` once as a
JavaScript module dashboard resource. No file copying is needed. Add:

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

## Accident wording refinement

The next revision labels explicit collisions/accidents with a nonempty, complete
body and no detected fire/smoke/extinguishing clues as “Baleseti jelentés · tűz
nincs említve”. This does not prove the absence of fire. Such candidates are
hidden in the focus view but retained under All reports. Missing/truncated text,
uncertainty and possible fire language block this categorization. Responding
firefighters alone are not a fire clue. No archive records are removed.
