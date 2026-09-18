# IGNIS public development roadmap

Status reviewed on 2026-09-16 against stable 0.26.5.

## Completed

- New public repository with clean initial history and source provenance.
- HACS repository switch exercised on one live installation with existing
  configuration/device identity and sampled history retained.
- Separate retrieval-result and snapshot-freshness fields in source details.
- Existing NSW/QFD calendars, location-specific distances, refresh deadlines and
  replay identity protection remain available.
- Geographic/location helpers and HA serialization have compatibility tests.

## Open limitations

- Migration checks sampled history; no exhaustive archive/database comparison
  or restore drill was performed. Dynamic marker counts are not fixed counts.
- Provider snapshot freshness does not establish a recent satellite pass at
  every location. Retrieval outages and old observations remain distinct.
- The parent integration package still imports Home Assistant. Basic models are
  not yet an independently installable SDK.
- Existing provider-specific coverage/access limitations remain in their source
  documents; integration availability is not an emergency all-clear.

## Next development sequence

1. Establish an independently consumable public basic-model boundary, preserving
   current imports, model identity, serialized fields and HA storage. Begin with
   an import/dependency inventory and a minimal package design; extract no full
   second engine and create no extra repository without a demonstrated need.
2. Verify standalone local monitoring with no Cloud account or private-package
   dependency. Keep compatibility tests for IDs, events and stored histories.
3. Begin every new provider/product with [access preflight](PROVIDER_ACCESS_PREFLIGHT.md).
   Notify the user of approval/registration requirements before substantial adapter
   work; prepare the request while independent development continues.
   Expand official Australian source coverage after checking official endpoints,
   usage terms, timestamps, geometry and attribution. Separate warnings, active
   incidents and planned burns; do not treat reports as satellite observations.
4. Assess other severely affected regions using the same source-quality gates.
   Country priority remains a research decision, not a promised rollout date.

Advanced service-side algorithms are outside this public roadmap. Optimization
remains paused. Each runtime change needs focused tests and release checks;
roadmap completion alone does not authorize deployment.
