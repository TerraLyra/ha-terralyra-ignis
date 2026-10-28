# 0.41.8 — Readable summary counters at larger text sizes

Summary counters now use text-relative column widths and wrap into separate rows when space is limited. This prevents the two explanations from colliding on narrow displays with enlarged text.

## Upgrade

Update in HACS and restart Home Assistant. Refresh the existing summary card resource using the administrator card-registration action (`card: summary`, `refresh_existing: true`), then reload the browser.

## Validation

The summary browser suite passed with Hungarian and English counter labels at 16px and 32px text on a 390px viewport. All 26 summary unit tests passed. Packaged frontend assets match their sources.

The change still needs a physical iPhone recheck after deployment. It does not add iOS Dynamic Type support. Card text follows the HA frontend language, custom titles remain user-defined, and forecast calendar text follows the HA system language; this release does not change those language choices.

Stable publication requires successful candidate checks, verified merged content and explicit user approval.
