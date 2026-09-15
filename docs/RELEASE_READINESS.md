# Release readiness

0.26.4 is the first release prepared for the new public repository. The source
provenance is recorded in SNAPSHOT_PROVENANCE.md. Main is protected by required
checks and pull-request review flow.

Release gates: tests and config-flow coverage, Python/JSON validation, HACS,
Hassfest, security checks and GOES ARM64/x86-64 compatibility.

HACS 2.0.5 accepts both repositories in its custom list. Registration has been
verified; a completed live package migration has not yet been verified. Follow
REPOSITORY_MIGRATION.md and preserve the existing configuration entry. The old
repository remains available for rollback.
