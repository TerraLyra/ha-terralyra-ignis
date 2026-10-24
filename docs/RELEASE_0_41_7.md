# 0.41.7 — Report focus recovery

When an open report disappears during a background update, its focused control is removed. The report dialog now moves keyboard focus to Close instead of losing it. Focus also falls back to Close if a previously focused action is no longer present, and remains usable when the report returns.

## Upgrade

Update in HACS and restart Home Assistant. Refresh the existing map card resource with the administrator card-registration action (`card: map`, `refresh_existing: true`), then reload the browser.

## Validation

The report-removal regression failed before the fix and passed afterward, including report recovery. The report-map browser suite and all 55 frontend unit tests passed locally. All 27 implementation PR checks passed, and the merged content matched the tested candidate.

Production removal/recovery has not been injected. The preceding 0.41.6 live check confirmed keyboard access to the license link and Escape return focus, but did not observe a report background refresh. Physical-phone and complete screen-reader acceptance remain open.

Publication requires completed release-candidate checks, verified merged content and explicit stable-release approval.
