# Release readiness

Stable 0.27.0 has been published, following 0.26.5. It adds optional NIFC
source diagnostics, calendar and map; see [release notes](RELEASE_0_27_0.md).
The manifest, changelog and README identify the same integration version. The
standalone model packaging pilot retains its independent experimental version.

Release gates: tests and 100% config-flow coverage, Python/JSON validation, HACS,
Hassfest, security, model packaging and GOES ARM64/x86-64 compatibility. Require
successful checks on the exact candidate commit before tagging a stable release.
Do not substitute earlier PR results for the candidate's results.

NIFC is opt-in and requires administrator first-use initialization. Initial live smoke validation on 2026-09-21 confirmed a later successful retrieval
and a sampled map/calendar match for location-relative distance and source time.
Full history equivalence, live restart/outage recovery and continuous uptime remain
unverified. Future upgrades should still check existing entities and sampled history.
Retain a backup. Do not delete history or storage to bypass initialization/recovery.
ACT/Victoria research does not enable production providers. Access approvals remain
separate release gates for those future providers. Issue #41 remains open.
