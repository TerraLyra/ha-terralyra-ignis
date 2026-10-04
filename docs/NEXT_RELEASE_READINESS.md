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

## Prepared 0.34.1 candidate

See [candidate release notes](RELEASE_0_34_1.md). Publication remains pending.
Included merged changes: #107 Canada diagnostics, #117 radius-form guidance,
#121/#124/#125 BM classification and offline review, and #122 Sentinel labels.
Candidate checks must pass before publication. Production patch acceptance remains
pending installation; 0.34.0 smoke checks above do not validate this patch.

## Remaining work

- Update the separately installed summary resource where the 0.33.0 file remains.
- #110: remaining usability work before wider HACS distribution.
- #41: historical counter investigation remains paused; no history deletion.

No release publication or HA restart is implied by this document.
