# 0.39.1 — Clearer map setup

Prepared for stable publication; not published yet.

## Changes

- The map editor offers Default, On and Off for marker clustering in Hungarian
  and English. Default removes the explicit override; unrelated settings remain.
  Turning clustering off can keep monitoring-circle centres separate. This is
  visual grouping, not incident matching.
- Map setup links open IGNIS settings and first-setup guidance in separate tabs.
- Resource setup errors explain the next step in English, Hungarian, German,
  Spanish, French and Italian. Error paths do not create resources.
- Isolated tests cover registration persistence, concurrent requests and delivery
  of every bundled card through HA HTTP, including version-query URLs.
- Offline BM review flags the vegetation phrase “bokros terület”; production
  satellite matching is unchanged and covered by a regression test.

## Upgrade

After publication, update through HACS, restart HA and fully reload the frontend.
Keep existing resource entries and card bindings. If an old editor remains visible,
update the existing resource URL query to `?v=0.39.1`, then reload. Do not register
a second copy. No source, notification or history migration is required.

## Validation boundary

Feature checks passed before merging. The final release candidate requires CI.
Automated isolated checks are not an unaided first-time-user installation trial.
No production HA configuration change or restart is part of release preparation.
