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
- A town centroid and RSS publication time alone cannot qualify a probable match.
  Explicit provenance and uncertainty must accompany spatial/temporal evidence.
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
