# BM context starts from satellite detections

BM notices enrich existing satellite incidents; they must not create satellite
incidents, change observation counts, trigger satellite alerts or establish fire
coordinates/status. This supersedes the experimental goal of deriving standalone
BM event locations. Existing user history and manually reviewed links remain.

`reports_for_incident` in report_context starts from an existing incident ID and
uses the complete bounded satellite population to preserve competing candidates.
It separates probable context from candidates requiring review. Probable is a
rule-based relationship label, not a calibrated probability or confirmation.

UI target: “Valószínűleg ehhez az észleléshez kapcsolódó BM-hír.” Keep the report
source, publication time and original text separately attributed. No match means
no matching context was found, never that the satellite observation is false.

## Remaining integration work

- Build BM evidence adapters around the satellite area and observation interval.
  Event-role mentions can support matching; responder towns, street-name matches,
  negated locations and unresolved corridors cannot supply precise coordinates.
- The user-approved BM policy accepts an explicit event-settlement identity plus
  nearby RSS publication as probable context, without requiring an exact event
  timestamp. The initial window is six hours before/after the satellite interval.
  Town identity is not a town-centre coordinate or a verified fire location.
- Re-evaluate links when notice content or incident identity changes. Do not save
  automatic links as manually approved records or overwrite existing reviews.
- Show context only on the satellite item. No BM-derived satellite entity/calendar
  event or satellite notification. Keep standalone RSS reading distinct from fire
  incident creation and preserve existing stored history.
- Validate competing nearby incidents, misleading responder names, stale notices
  and publication-versus-event time before enabling automatic display.

The lookup function is implemented and has focused checks. Automatic BM extraction,
persistence and frontend wiring are not yet enabled. Existing manual review actions
remain backward-compatible during this transition.

## Town/time matching implementation

`bm_satellite_context.bm_reports_for_satellite` implements this policy separately
from legacy manually reviewed coordinate matching. BM reports need explicit event
settlement IDs in the same gazetteer namespace as the satellite assignment and
fire relevance. Empty event-place sets (including responder-only notices) do not
match. Competing satellite IDs are returned with an ambiguity flag without
removing the probable label. No real probability is claimed.

The extraction adapter must still establish event-role IDs rather than passing
all mentioned towns. That adapter and frontend display are not yet connected;
this function alone does not enable automatic production links. Existing manual
links and satellite history remain unchanged.

## Experimental evidence adapter

The offline NLP probe now emits `satellite_context_evidence` via
`bm_event_town_adapter`. It requires an unambiguous gazetteer ID, a locative or
near-town construction inside positive fire evidence, and no conflicting
responder/organization/direction/street/negation/corridor role. Unknown mentions
alone are insufficient. Original mention and fire-clause evidence are retained.

Saved 92649 replay passes Hejőbába (not the responding town); 92648 rail accident
produces no fire-place evidence. This is a regression check, not a new holdout.
The adapter does not derive coordinates or create incidents. Multi-town corridors
remain unlinked rather than being reduced to either endpoint. Runtime source
fetching, compatible satellite gazetteer IDs and display wiring remain pending.

## Satellite settlement identity audit

The offline `bm_settlement_identity` bridge joins a *selected settlement record*
from cities500 to the HU supplement by exact name, country and centre coordinates.
It never substitutes the satellite position with a settlement centre. Same-name
places, changed coordinates, non-HU records and duplicate identities do not get
an inferred ID. This is a record identity check, not municipality-boundary proof.

The packaged snapshots contain 1,226 HU cities500 records: 1,075 join uniquely;
142 names are absent from the supplement and 9 have differing centre coordinates.
These 151 records remain unresolved. No network lookup or database replacement is
performed. A nearest settlement is still not proof that a detection falls inside
that municipality; the context relationship remains heuristic.

Runtime geocoding now exposes the selected settlement centre, country and distance
in optional PlaceInfo fields. Existing three/four-argument callers remain valid.
An isolated replay of the actual async resolver checks the shared-record bridge
with the packaged databases and an offset observation. Persisting that provenance,
applying the bridge in the coordinator and connecting the BM evidence adapter
remain necessary before automatic display.
The offline bridge is not enabled in HA. The research suite passes 129 checks;
these cover contracts/regressions, not calibrated matching accuracy.

## Current-text context adapter

`report_from_current_notice` checks title and description against the analyzed
text before creating the bounded pure context report. A changed or explicitly
truncated description cannot reuse the analysis. Publication time comes from the
current notice and must be timezone-aware. The returned match includes original
RSS text, BM OKF attribution and an explicit automatic-heuristic method label.
Consumers must render this text as text, never interpolate it into HTML.
Manual review storage is neither read nor written by this adapter.

This remains offline research: the HuSpaCy model is not bundled or enabled in HA.
Choosing a lightweight runtime adapter versus an optional local model remains a
separate deployment decision. Context matching does not require a model itself.
