# 0.27.1 — source health alongside fire counts

Published as stable v0.27.1 on 2026-09-21.

## What changes

Current fire counts now expose whether their source retrieval is available,
delayed, partial, unavailable or unknown. This makes a count drop caused by a
missing source easier to distinguish from a change in the received observations.
The numeric counting method is unchanged.

Active/combined cluster counts and raw pixel counts summarize their assigned
sources. The FIRMS cluster count reports only FIRMS health. Attributes include
`source_retrieval_status`, `source_statuses`, `unavailable_sources` and
`delayed_sources`. The delayed-only usable state is named `degraded`.
`observation_completeness` remains `not_established`: successful retrieval does
not establish complete satellite coverage, and cached observations may still
contribute during an outage.

## Upgrade and check

1. Retain a Home Assistant backup before updating.
2. Update through HACS and restart Home Assistant.
3. Confirm version 0.27.1 and inspect an existing count entity's attributes.
4. Check that existing locations, entity identities and sampled history remain
   accessible. No storage reset, history deletion or NIFC reinitialization is needed.

No new provider is enabled, no storage migration is introduced, and no entity
identity or configuration is changed. Optimization remains paused. Providers
awaiting permission or timestamp evidence remain outside production.

## Validation and limits

Automated regression covers full → partial → recovered source responses after a
restart while preserving incident history, plus missing and delayed source health.
All 12 required checks passed on the exact release commit before publication.
Sampled live verification of all three count types passed after installation;
do not deliberately interrupt production sources to reproduce an outage.

The original September 10 counter discontinuity (#41) remains unresolved. These
source diagnostics do not establish its historical cause.
