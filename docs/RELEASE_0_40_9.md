# 0.40.9 — Source receipt times and keyboard focus

The location-summary editor shows each source's last successful data receipt in
the Home Assistant timezone. Missing or timezone-less values remain unknown;
invalid formatting settings fall back to explicitly labelled UTC. The review
explains that receipt time is not satellite observation time and does not prove
freshness. Delayed and failed source states remain visible; unavailable location
sensors suppress retained source details.

Background updates to the same location's setup review preserve keyboard focus
on the notification-blueprint guide. They do not take focus from other controls.
Source details continue to update normally.

## Validation

Implementation PRs #211 and #212 each passed all 27 automated checks. All 50
frontend unit tests pass. Browser coverage checks HA timezone rendering, updated
receipt text, retained guide focus, outside-focus preservation and unfinished
title edits. The release candidate has not been installed on production HA.

## Update

Update through HACS, restart Home Assistant and fully reload the browser or
Companion App frontend. Keep existing card resources and dashboard configuration.
For stale manually registered resources, follow
[resource recovery](CARD_RESOURCES.md#later-updates-and-rollback).

Inspect the location-summary editor's per-source receipt times. Keyboard users
can focus the blueprint guide while source details update. No configuration save
is required to inspect the changes. This release does not enable providers, alter
polling, send notifications or change radii, bindings or history. No storage
migration is required.
