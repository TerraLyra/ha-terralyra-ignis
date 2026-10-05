# 0.35.0 — Dashboard cards bundled with IGNIS

## Changes

The three optional dashboard cards are now included in the integration package.
After a one-time change of their resource URLs, HACS updates the matching card
files with IGNIS. Existing dashboard card configuration is retained.

BM report classification now recognizes kitchen fires as local-asset candidates
and grass spreading to a garage as mixed candidates. Nearby buildings mentioned
in another sentence do not alone establish spread. Unknown and mixed reports
remain in the default view; no official incident status or burned area is inferred.

Offline research gains reviewed Hungarian place aliases and JAXA WLF date/CSV
preflight checks. These do not enable automatic BM coordinates or a live Himawari
source. WLF decoding still requires a real current file sample.

## Upgrade

1. Update through HACS and restart Home Assistant at a suitable time.
2. For each optional IGNIS card already in use, **edit its existing dashboard
   resource URL**, retaining JavaScript module type. Do not add a duplicate.
   Use `/terralyra_ignis/cards/ignis-location-summary.js`,
   `/terralyra_ignis/cards/ignis-report-map.js` or
   `/terralyra_ignis/cards/ignis-bm-reports.js` as appropriate.
3. Fully reload each browser or Companion App frontend. Already-open pages keep
   the previously loaded code until reloaded. Later HACS updates require no
   manual card-file copying once these URLs are in use.

Native HA maps need no IGNIS resource. Existing `/local/` resources continue to
use their local files until explicitly migrated. We do not rewrite resources,
delete old files or modify dashboard YAML automatically. The notification
blueprint remains separately imported; existing automations are unchanged.
User history, location identities, radii, source opt-ins and review holds remain.

See [card setup and rollback](CARD_RESOURCES.md). Rolling back to 0.34.1 or older
requires restoring the old resource URLs and matching local files, because those
versions do not serve the bundled URLs.

## Validation

Feature PRs #127–#129 passed all 27 checks. BM checks cover 86 offline cases;
WLF preflight has eight synthetic tests. Candidate CI must pass before publication.
Live acceptance of the new resource URLs remains pending installation. No HA
restart, automatic resource migration or test notification was performed.
