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

## Published 0.36.0

Stable [v0.36.0](https://github.com/TerraLyra/ha-terralyra-ignis/releases/tag/v0.36.0)
was published from `bdcf628db109195928b646a843658b1c1b977456`.
The merged tree matched the candidate that passed all 27 checks.
See [release notes](RELEASE_0_36_0.md). Includes source guidance, visual map editing
and binding status, offline BM fixes, and updated onboarding.

After the user confirmed update and restart, the integration page showed 0.36.0.
The bundled summary JavaScript matched the released file, but the browser retained
older card code. Updating the two existing summary/map resource URLs with
`?v=0.36.0` and reloading the dashboard made the new delayed-source guidance
visible in both sampled location summaries. No additional HA restart was needed.
See [browser cache recovery](CARD_RESOURCES.md).

This is a sampled live check, not clean-install acceptance or verification of every
editor interaction, notification delivery, language or history continuity.

## Published 0.38.0

Stable [v0.38.0](https://github.com/TerraLyra/ha-terralyra-ignis/releases/tag/v0.38.0)
was published from `c8f95fefc965bd5a779425955497d9c0202e2675`.
After the user upgraded and restarted, a sampled read-only check on HA 2026.10.0
confirmed summaries, forecasts, radii and visual editors rendering. This is not
full clean-install or notification-delivery acceptance.

## Prepared 0.38.1

Contains PRs #153 and #154: summary location choices, saved Home forecast wording,
and explicit QFD Web Mercator conversion. See [release notes](RELEASE_0_38_1.md).
Feature checks passed; the exact release candidate must pass CI before tagging.
The saved QFD feed yielded 42 records with zero invalid records offline. Production
QFD recovery is not yet verified. Canada's existing review hold remains unresolved;
no protection reset or live configuration change is part of this release.

## Remaining work

- [Public onboarding acceptance](ONBOARDING_ACCEPTANCE.md): distinguish delivered
  building blocks from first-time-user acceptance that has not yet been performed.
- #110 remains open for the guided setup and dashboard usability work.
- #41: historical counter investigation remains paused; no history deletion.

No release publication or HA restart is implied by this document.
