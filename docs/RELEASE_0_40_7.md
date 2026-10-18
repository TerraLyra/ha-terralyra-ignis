# 0.40.7 — Persistent NIFC failure diagnostics

NIFC review pauses already survived restarts, but their detailed cause did not.
Source diagnostics now expose `last_failure_reason` and
`last_failure_http_status`, preserving them alongside the cooldown checkpoint.
Only allowlisted local descriptions and HTTP status codes are retained; arbitrary
exception text and response bodies are excluded.

Controlled recovery preserves existing wait bounds and retains the diagnostic
reason until a successful retrieval clears it. Legacy cooldown checkpoints remain
supported. The update cannot reconstruct reasons lost before installation.

## Validation

Implementation PR #205 passed all 27 automated checks. The 117 standalone NIFC
tests cover legacy checkpoints, failure restart round trips, sanitization, HTTP
waits, controlled recovery and successful retrieval clearing the failure details.
The new release candidate has not been installed on production Home Assistant.

## Update

Update through HACS and restart Home Assistant. No dashboard change or storage
reset is required. Diagnostic checkpoints use an extended format after a failure;
keep the updated integration when such a checkpoint exists rather than manually
editing or resetting it to accommodate an older version.

Existing pauses are not automatically cleared. Review diagnostics and use the
explicit NIFC recovery action where appropriate; all known waits remain in force.
No provider is enabled by this update and stored incident history is unchanged.
