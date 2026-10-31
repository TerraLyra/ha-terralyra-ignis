# 0.41.10 — BM appliance-fire review clues

The offline BM review recognizes the reviewed adjective békéscsabai as Békéscsaba. Individual and listed fire-brigade references retain their responder context rather than becoming verified incident locations.

The shared fire-scope review classifier recognizes washing-machine fires as local-asset fire candidates. Negated statements, exercises, truncated input and appliance mentions without fire evidence remain unclassified. This is a review clue, not confirmation of an active fire or a new alert rule.

## Upgrade

Update in HACS and restart Home Assistant. No dashboard-card regeneration or configuration changes are required for this patch.

## Validation

All 27 implementation PR checks and all 147 local BM tests passed. Replaying RSS 93285 resolves Békéscsaba and identifies a local-asset fire candidate; the Dombóvár accident remains a non-fire candidate. Regression tests cover responder lists, differing incident and responder towns, negation, exercises, truncation and word boundaries.
