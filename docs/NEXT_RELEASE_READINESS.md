# Next release readiness

Reviewed 2026-09-21. Stable release remains 0.27.0; 0.27.1 is the prepared, unreleased
maintenance candidate, not authorization to publish or deploy.

## Included changes

- #48–49: current roadmap, scoped live NIFC evidence and HA camera test dependency.
- #50: full → partial → recovered retrieval after restart preserves incident history.
- #51: active/combined counts, FIRMS counts and raw pixels expose source retrieval
  status without changing numeric semantics. FIRMS diagnostics are source-scoped.

No new provider, storage migration, entity renaming, optimization or SDK publication
is included. Victoria, ACT and other pending providers remain outside production.

## Evidence and remaining steps

All GitHub checks passed for #51 at commit
`72611826d2830f4f52b0602939827b6f22024f08`, subsequently merged as
`f7b1505d36e6da35d535dda582838ca56ccca68e`. CI covers the restart regression,
unknown/delayed/unavailable source health and existing count behavior.

1. Manifest version 0.27.1 and matching [release notes](RELEASE_0_27_1.md) are
   prepared. Validate this exact candidate with the required CI checks. Publication
   authorization remains a separate step.
2. Publish only after that candidate is green. No tag or release is created by this document.
3. After user-approved installation, inspect count attributes in HA: available
   sources should be reported; FIRMS attributes should contain only FIRMS health.
   Do not deliberately disable live providers to simulate an outage. The automated
   regression covers that transition without disturbing production.
4. Confirm existing entity identities and retained history remain accessible.
   Record the scope of sampled checks rather than claiming full history equivalence.

Issue #41 remains open: reproduced failure modes and clearer diagnostics do not
prove the original September 10 cause. Further attribution needs contemporaneous
logs/raw source evidence if available; it must not require deleting user history.
