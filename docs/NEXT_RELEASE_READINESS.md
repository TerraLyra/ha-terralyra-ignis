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

## Published 0.35.0 and 0.35.1

Stable 0.35.0 bundled the optional dashboard cards and shipped BM classification
improvements and offline WLF preflight checks. Existing dashboard resource URLs
were migrated to the bundled routes; the dashboard subsequently rendered.
See [0.35.0 notes](RELEASE_0_35_0.md).

Stable 0.35.1 was published from `178ca30644d1b797f11d82ada125f29f719cabd0`.
The merged tree matched the candidate that passed all 27 checks. It adds small
decorative summary icons. The user confirmed update and restart; a subsequent
read-only dashboard check found location summaries and forecasts rendering.
This does not independently verify every icon, notification delivery or history
continuity. See [0.35.1 notes](RELEASE_0_35_1.md).

## Main branch after 0.35.1

- #132 adds actionable source-state guidance to the summary card. This is merged
  but not included in the published 0.35.1 package.
- #133 updates English/Hungarian onboarding and card installation documentation
  for bundled resources. These instructions are available on the main branch.

## Remaining work

- [Public onboarding acceptance](ONBOARDING_ACCEPTANCE.md): distinguish delivered
  building blocks from first-time-user acceptance that has not yet been performed.
- #110 remains open for the guided setup and dashboard usability work.
- #41: historical counter investigation remains paused; no history deletion.

No release publication or HA restart is implied by this document.
