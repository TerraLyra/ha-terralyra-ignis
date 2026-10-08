# BM reports as satellite context

The optional IGNIS report-map card can show a BM OKF report when a user opens an
existing satellite marker. It labels the report as probably related, displays the
original RSS text, source link and publication time, and discloses competing
satellite candidates. Native Home Assistant entity details remain accessible.

## How to use it

Use the bundled `ignis-report-map` card. Retrieve BM reports with the existing
BM reports card first: the satellite popup reads only the local report archive.
It does not refresh RSS or download article pages. An empty archive or no match
produces an explicit no-related-report message, not a statement that no fire exists.

## Matching limits

- The existing nearest-settlement resolver supplies the satellite town. Its name
  and centre must match a unique record in the packaged Hungarian GeoNames table.
  This is a nearby-town heuristic, not proof of municipality boundaries.
- Lightweight rules require a locative/near-town expression in a positive fire
  clause. Responder clauses, negation, exercises, ambiguous town names and truncated
  descriptions are excluded. Unsupported wording simply remains unmatched.
- RSS publication must be within six hours before the first or after the last
  satellite observation. Publication is not claimed to be the fire's start time.
- The newest 100 valid archived reports and at most 500 satellite incidents are
  considered. The current gazetteer snapshots have 1,075 exact HU record matches
  out of 1,226 cities500 records; the remaining records are not guessed.
- “Probable” is a heuristic association, not a calibrated percentage or official
  confirmation. A report can fit multiple satellite incidents.

No BM notice creates a satellite incident, changes fire coordinates/counts/status,
or triggers a satellite notification. Existing manual reviews remain separate.
The read-only archive snapshot does not save, expire or delete stored records.

## Implementation and validation

`get_satellite_report_context` runs local gazetteer work in the executor. The map
card requests context on selection, renders report text as text, and rejects
unsafe source links. Automatic associations are recomputed rather than saved as
manual approvals. The runtime has no HuSpaCy/spaCy/model dependency or download.
Optional NLP experiments under `tools/source_research` are development-only.

Local checks: 137 BM research/runtime tests, 32 frontend tests, browser popup
checks and 112 targeted HA tests. Production installation acceptance is separate.
The feature scope is closed; wider language coverage and general NLP are deferred.
