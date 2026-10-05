# Release validation and remaining work

## Published 0.34.0

Stable [v0.34.0](https://github.com/TerraLyra/ha-terralyra-ignis/releases/tag/v0.34.0)
was published from `adffc819cb44cfdb37ac70d2395720933128daec`.
The merged tree matched the candidate that passed all 27 checks.
See [release notes](RELEASE_0_34_0.md) for changes and upgrade instructions.

## Sampled live validation on 2026-10-03

After user-confirmed update and restart, the integration page reported 0.34.0
without a visible setup error. The dashboard displayed shared-fire markers with
explicit provider names and a possible-association label. Location summaries
rendered both radii, source health and explicitly bound forecasts.

The optional summary resource was still the 0.33.0 JavaScript file. Its existing
summary rendered, but this does not validate the 0.34.0 visual editor in production.
That file requires a separate resource update and browser reload. No live
configuration, automation or history was modified during these checks.

These observations are a limited smoke check, not proof of continuous uptime,
full history equivalence or correct association of every physical fire. Notification
delivery and every language were not exercised live. No test push was sent.

## Published 0.34.1

Stable v0.34.1 was published from `61db1eb758b3d3dee4dfdccaa4c4a2d0db53b6f0`.
After the user updated and restarted, the integration page showed 0.34.1 without
visible setup errors. The dashboard rendered Sentinel-3A/B names and both radii;
IODC remained delayed. This is a sampled smoke check, not complete live acceptance.

## Prepared 0.35.0 candidate

See [candidate notes](RELEASE_0_35_0.md). Includes #127 bundled cards, #128 offline
WLF preflight and #129 BM fixes. Publication requires successful candidate checks
and explicit approval. New bundled URLs still require live acceptance after update.

## Remaining work

- Migrate existing optional card resources to bundled URLs after installing 0.35.0.
- #110: remaining usability work before wider HACS distribution.
- #41: historical counter investigation remains paused; no history deletion.

No release publication or HA restart is implied by this document.
