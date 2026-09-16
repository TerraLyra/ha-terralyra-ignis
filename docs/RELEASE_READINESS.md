# Release readiness

Stable 0.26.4 established the new public repository; stable 0.26.5 adds source
health details. Source provenance is recorded in SNAPSHOT_PROVENANCE.md. Main
is protected by required checks and the pull-request flow.

Release gates: tests and config-flow coverage, Python/JSON validation, HACS,
Hassfest, security checks and GOES ARM64/x86-64 compatibility. These passed for
0.26.5. That release was installed and its new fields checked on a live HA.

The HACS 2.0.5 repository switch has been exercised on one installation with
identity and sampled-history checks. It was not a full database equivalence or
restore test. See REPOSITORY_MIGRATION.md for the sequence and limitations.
The old repository remains available for rollback.
