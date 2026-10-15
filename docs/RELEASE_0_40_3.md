# 0.40.3 — Satellite observation summaries and TasALERT receipt times

Selecting an IGNIS satellite marker in the optional report-map card now opens a
settlement-first summary: first/latest observation times, related BM news,
source associations, then collapsed technical details. The native Home Assistant
entity dialog remains available through a separate button. Standard map cards
retain their native behavior. Background updates preserve keyboard focus and
expanded details; reopening starts with details collapsed.

Observation times are not ignition or extinction times. Related news and
multiple-source associations are probable links, not official confirmation.
The interface supports Hungarian and English fallback.

TasALERT diagnostics and markers now expose a persisted `last_success_at`.
Accepted HTTP 200 and valid 304 responses update it; failures preserve the last
successful time. Existing storage loads without an invented timestamp and gains
one after the next scheduled successful response. Source freshness remains
`not_established`: successful retrieval does not establish current fire activity.

Update through HACS, restart Home Assistant, then fully reload the browser.
For cached manually registered resources, follow [card resources](CARD_RESOURCES.md).
No storage reset, history deletion or forced source request is needed.

Validation before release preparation: 43 frontend unit tests, browser regressions,
55 offline TasALERT tests and complete CI passed on the implementation PRs
#189–#191. A live multi-source summary was inspected before the focus refinement.
The receipt-clock change has not yet been validated on the user's live HA.
