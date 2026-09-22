# 0.28.0 — optional Canadian official reports

Release candidate preparation; not yet published.

## Included

- Canadian CWFIF official source-status sensor, optional map and disabled-by-default
  calendar, separate from satellite detections.
- Local filtering around monitored places and distances relative to the matching
  place; stable identity based on agency and national fire ID.
- Explicit administrator initialization/recovery, bounded downloads, persistent
  request pauses and storage-timeout protection shared across consumers.
- Reported status timestamps with explicit offsets; attribution and licence links.

See [Canada setup and interpretation](CANADA_USAGE.md).

## Upgrade

Keep a HA backup, install the release through HACS and restart. Check the installed
version, existing locations and sampled history before enabling Canada. No reset,
existing-provider reinitialization or history migration is required. Canada is opt-in.

## Validation and limits

The feature PRs passed full HA, source-research, HACS, Hassfest and security checks.
The Canada standalone suite has 63 tests. The exact release-candidate CI must also
pass before publication. Canada has not yet been validated in the user's live HA;
that check follows installation and deliberate activation, without deleting data.

The source does not establish national completeness or current fire activity.
Map/calendar retention represents the current cached response, not a new incident
archive. Optimization remains paused. ACT and providers awaiting approval remain
outside this release. The original count discontinuity (#41) is still unresolved.
