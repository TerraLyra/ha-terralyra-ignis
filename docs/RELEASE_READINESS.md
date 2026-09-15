# Migration snapshot readiness

This is a local staging snapshot, not a new release. The original manifest
version 0.26.3 is preserved for comparison and must not be treated as a new
published release tag. See SNAPSHOT_PROVENANCE.md.

Required before distribution: clean initial history; verified public target;
working security reporting; CI/HACS/Hassfest on the target; validated HACS
repository-switch instructions and rollback with unchanged HA IDs/history.

The original repository remains available. No live HA migration is performed by
preparing this snapshot. Test results for the source commit do not substitute
for running checks on this tree. Local check results are recorded outside the
public snapshot until verified.
