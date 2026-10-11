# 0.39.2 — Cleaner dashboard setup

Prepared for stable publication; not published yet.

## Changes

- Report-age controls and their explanatory note stay hidden when no bound official
  report source is enabled. Re-enabling a source restores the selected age filter.
- The English one-day option reads “Within 1 day”.
- Summary card picker metadata uses English, consistent with the map picker.
  Card content still follows its existing Hungarian/English language handling.
- The README links to the current stable release instead of a stale version label.

## Upgrade

After publication, update through HACS, restart HA and fully reload the browser or
Companion App frontend. Keep one resource entry per card and existing bindings.
If cached code persists, update the existing resource query to `?v=0.39.2`.
No provider, alert-rule or history migration is needed.

## Validation

The underlying changes passed 39 frontend tests, isolated Chrome checks and CI.
The versioned release candidate must pass CI before publication. The assisted
clean-install trial is recorded in [onboarding acceptance](ONBOARDING_ACCEPTANCE.md);
unaided-user acceptance and real phone delivery remain unverified.
