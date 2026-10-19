# 0.40.10 — Sentinel-3 failure diagnostics

Sentinel-3A and Sentinel-3B now expose safe diagnostic codes that distinguish
network failures, server errors, timeouts, rate limits, invalid responses and
other request failures. Previously these failures could have an empty diagnostic
code. Only predefined codes are exported; raw exception messages are not used
as diagnostic codes.

The codes appear in provider-health and location source-health attributes.
Existing failure states and retry timing, including Retry-After, are preserved.
This improves diagnosis; it does not itself restore an unavailable upstream service.

## Validation

Implementation PR #214 passed all 27 automated checks. All 519 offline source
tests passed locally, including six transport scenarios for each satellite and
rejection of unknown diagnostic codes. The release candidate has not been
installed on production Home Assistant.

## Update

Update through HACS and restart Home Assistant. No dashboard changes or storage
migration are required. After the next scheduled Sentinel-3 retrieval, inspect
`diagnostic_code` in source-health attributes if a failure persists. Do not bypass
the normal retry wait. This release does not change monitoring radii, notification
settings, enabled sources or history.
