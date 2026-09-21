# 0.27.1 release validation and remaining work

Stable [v0.27.1](https://github.com/TerraLyra/ha-terralyra-ignis/releases/tag/v0.27.1)
was published on 2026-09-21 from commit
`364d9ecb16acb58cb4d818a1e0e3e85cc54add37`. All 12 checks on this exact commit
completed successfully before publication.

## Delivered

- #48–49: current roadmap, scoped live NIFC evidence and HA camera test dependency.
- #50: full → partial → recovered retrieval after restart preserves incident history.
- #51: active/combined counts, FIRMS counts and raw pixels expose source retrieval
  status without changing numeric semantics. FIRMS diagnostics are source-scoped.
- #53: aligned 0.27.1 manifest and release notes; candidate CI also passed.

No new provider, storage migration, entity renaming, optimization or SDK publication
is included. Victoria, ACT and other pending providers remain outside production.

## Sampled live validation

Following user-confirmed installation/restart, the HA integration page reported
0.27.1. Read-only checks on 2026-09-21 confirmed:

- Combined cluster count exposes degraded retrieval with a delayed source.
- FIRMS cluster count exposes available retrieval and only FIRMS source health.
- Raw pixel count exposes degraded retrieval; its attributes updated after the
  numeric state last changed, with additional source delay visible.
- All three expose observation completeness as not established; no unavailable
  sources were listed at the sampled times.

Samples were taken at different times and are not synchronized snapshots. No
production source was deliberately interrupted and no configuration or history
was changed during validation. Full history equivalence, live outage/recovery
and continuous uptime have not been established.

## Remaining work

Issue #41 remains open: reproduced failure modes and clearer diagnostics do not
prove the original September 10 cause. Further attribution needs contemporaneous
logs/raw source evidence if available; it must not require deleting user history.

Provider requests remain pending review. Implement a further provider only after
its product-specific access terms and required timestamp/schema evidence are
settled. No follow-up version is promised or authorized by this document.
