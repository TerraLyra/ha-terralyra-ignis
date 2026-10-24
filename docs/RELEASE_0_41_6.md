# 0.41.6 — Report keyboard focus

## Preserve keyboard focus during report updates

- Keep focus on the report license link when new data redraws the report card.
- Extend browser regression checks for keyboard marker activation, technical details, Escape/Close return focus and BM list navigation.
- Reconcile the development roadmap with delivered functionality and the remaining acceptance checks.

## Upgrade

Update in HACS and restart Home Assistant. Refresh the existing map card resource with the administrator card-registration action (`card: map`, `refresh_existing: true`), then reload the browser.

## Validation boundaries

The focus regression failed before the fix and passed after it. Existing report-map and BM browser suites and 55 frontend unit tests passed locally. Sampled live 0.41.5 keyboard navigation passed; the new license-link fix still requires post-upgrade acceptance. Physical-phone and complete screen-reader acceptance remain open.

Publication requires completed candidate checks, verified merged content and explicit stable-release approval.
