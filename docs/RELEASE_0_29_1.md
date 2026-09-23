# 0.29.1 — NIFC retrieval time and readable incident titles

- NIFC report markers expose the actual UTC time of the last successful retrieval.
  Failed refreshes retain the previous time. After restart it stays unknown until
  a new successful response; cooldown timing remains independent of wall clocks.
- The optional report map dialog uses the NIFC incident name when provided,
  with the existing title as fallback. Source text is rendered as plain text.
- BM OKF location research tools reuse the bundled GeoNames database but remain
  offline only: no automatic location association, new entities or map markers.

## Update

Update through HACS and restart Home Assistant. No reinitialization, history
reset or configuration migration is required. Wait for a successful NIFC response;
its persisted cooldown can delay the first request after restart.

The optional card is a separate download: copy the attached `ignis-report-map.js`
over the installed card file and change its existing dashboard resource query to
`?v=0.29.1`, then reload the browser. Keep one resource entry. HACS does not update
this dashboard file automatically. If the incident-name card from PR #64 is
already installed, its code is unchanged in this release.

## Validation and limits

The NIFC receipt change passed the full HA, HACS, Hassfest, security and
compatibility checks before merge. Offline checks cover success, failure and
restart semantics; the HA map test covers the exposed timestamp. Incident-name
presentation was checked in live HA. Receipt-time display requires a post-upgrade
live check. Missing source descriptions remain explicitly missing.

No new provider permissions are assumed. Optimization remains paused. Existing
entity identities, monitored locations and recorded history are preserved.
