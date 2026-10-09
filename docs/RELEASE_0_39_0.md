# 0.39.0 — Easier optional card setup

Published as stable [v0.39.0](https://github.com/TerraLyra/ha-terralyra-ignis/releases/tag/v0.39.0).

## Changes

- An administrator can review optional dashboard resources and explicitly register
  one missing card module through `terralyra_ignis.register_dashboard_card`.
  Confirmation is off by default. Existing, duplicate or legacy entries are not
  overwritten or removed. YAML-managed resources require manual configuration.
- Summary location choices show readable names, retaining technical IDs only to
  distinguish identical names. Existing bindings are preserved.
- The summary editor links to location settings and first-setup help in separate
  tabs. Registration and help links do not create dashboard cards or notifications.
- Registration action guidance is available in English, Hungarian, German,
  Spanish, French and Italian.
- Canada diagnostics distinguish a retained HTTP client error from an unknown
  prior review cause. No existing hold is cleared automatically.

## Upgrade and optional setup

1. Update through HACS, restart HA and fully reload the frontend.
2. Keep existing resources. If old card code persists, update the existing resource
   query to `?v=0.39.0`; do not create duplicate entries.
3. Existing working cards need no re-registration. For a missing optional card,
   run the new action without confirmation first, review the result, and follow
   [resource setup](CARD_RESOURCES.md). Check for renamed copies before confirming.
4. After registration, add the card to the dashboard and select the desired place.

No new data provider, language model, history migration or notification change.
No live Home Assistant restart or configuration modification is part of preparation.

## Validation and limits

Feature PR checks passed. Fifteen targeted resource planner/service tests include
administrator access, preview, repeated registration, YAML mode and a real HA
resource collection. Thirty-nine frontend tests and isolated Chrome checks cover
summary behavior and setup links. The exact release candidate must pass CI before
publication. Live registration acceptance and an unaided clean-install trial are
still outstanding; automated tests do not establish these.
