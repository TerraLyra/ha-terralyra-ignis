# 0.40.8 — Clearer summary setup

The location-summary card editor now shows readiness and troubleshooting guidance
for each source belonging to the explicitly selected location. If the location
sensor becomes unknown or unavailable, retained source statuses are suppressed
rather than displayed as current. Missing source status remains explicitly unknown.

The setup review also links directly to the Hungarian or English notification
blueprint instructions. The guide opens in a separate tab, preserving unfinished
card edits. The editor explains that a HACS update does not create a phone
notification automation; phone and message-language selection remain user steps.

These are read-only setup improvements. They do not enable providers, import
blueprints, send notifications or change existing card bindings, radii or history.

## Validation

Implementation PRs #207 and #208 each passed all 27 automated checks. All 49
frontend unit tests pass. Browser regressions cover changing source states,
unavailable-sensor suppression, both guide languages and unchanged card
configuration. The release candidate has not been installed on production HA.

## Update

Update through HACS, restart Home Assistant and fully reload the browser or
Companion App frontend. Keep existing card resources and dashboard configuration.
If a manually registered resource stays stale, follow
[resource recovery](CARD_RESOURCES.md#later-updates-and-rollback).

Open a location-summary card's visual editor and review source readiness and the
notification-blueprint guide. No configuration save is needed merely to inspect
these additions. No storage migration is required.
