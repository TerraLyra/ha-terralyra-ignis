# 0.41.2 — Refresh existing dashboard cards

After an integration upgrade, a browser can continue displaying an older
bundled card. The existing administrator-only dashboard setup action now offers
**Refresh an existing bundled card**. It updates the module's URL using a hash
of the installed card contents; reload the browser afterwards.

This supports the report map, location summary and BM report card. It keeps the
resource ID, never adds a card in refresh mode, and makes no change on repeated
refreshes with identical contents. Missing, duplicate, legacy, wrong-type and
YAML resources require separate review. Nothing is rewritten at startup.

## Validation and update

Real Home Assistant collection tests cover identity preservation and repeated
refreshes. Negative tests cover the protected inventories and simultaneous add
confirmation. Full CI must pass before publication.

Update through HACS and restart Home Assistant. To verify the new action, select
a bundled card in Developer Tools → Actions, enable refresh, run the action and
reload the browser. Repeating the action should return `changed: false`.
