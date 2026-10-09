# 0.38.1 — Queensland reports and summary fixes

Published as stable v0.38.1 on 2026-10-08 (UTC).

## Changes

- Read Queensland reports whose feed explicitly declares EPSG:3857 coordinates.
  Points and warning polygons are converted to geographic coordinates. Existing
  geographic feeds remain supported; unknown coordinate systems are rejected.
- Show only location summary sensors in the visual location selector, removing
  misleading duplicate source-count entries.
- Label saved legacy Home forecast bindings clearly instead of suggesting that
  a new forecast must be enabled. Forecast validity remains visible separately.

## Upgrade

1. Update through HACS and restart Home Assistant when convenient.
2. Fully reload the browser or Companion App frontend.
3. If old card code persists, change the existing resource query to `?v=0.38.1`;
   do not add duplicate resources.
4. Check the Queensland calendar if enabled, and review summary location choices.

No new provider, dependency or language model is added. Location radii, source
opt-ins, history, notification rules and Canada's existing review hold are unchanged.

## Validation and limits

The feature changes passed GitHub CI. Targeted QFD tests covered 24 parser, client
and calendar cases. The saved official feed parsed 42 records with zero invalid
records. Summary changes passed 38 frontend checks and isolated browser tests.
The release candidate passed all CI checks; the merged tree matched the tested
candidate. After upgrade, a sampled live check confirmed QFD availability with
zero invalid records and corrected summary choices and saved Home wording.
This does not establish continuous source availability or complete onboarding
acceptance.
