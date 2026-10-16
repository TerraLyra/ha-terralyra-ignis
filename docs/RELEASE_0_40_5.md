# 0.40.5 — Easier map setup and recovery

A failed map load now offers a retry button with Hungarian and English guidance.
Retry rebuilds the frontend card without fetching provider data. Late results from
an older load attempt cannot replace a successfully loaded map.

The location summary and its editor distinguish missing sensors, unsupported
sensors and sensors associated with another location, with actionable guidance.
A correctly associated sensor with unavailable data remains a data-availability
issue rather than a configuration error.

The visual map editor offers 16:9, 4:3 and square aspect ratios plus a scale ruler.
Existing custom ratios are preserved; Default removes only the chosen override.
In sections dashboards, Layout settings may also affect card dimensions.

These changes do not modify provider configuration, notification radii, entity IDs
or stored observations. No storage migration is required.

## Validation

Implementation PRs #197–#199 each passed all 27 automated checks. The latest
frontend suite contains 47 passing unit tests. Browser tests exercise failed-load
recovery, superseded failures, custom-ratio preservation and appearance changes.
The release candidate has not been installed on production Home Assistant.

## Update

Update through HACS, restart Home Assistant, then fully reload the browser or
Companion App frontend. Existing dashboard configuration is retained. If a manually
registered resource remains stale, use [resource recovery](CARD_RESOURCES.md#later-updates-and-rollback).

After updating, verify the summary location and source status, open an observation
on the map, and preview the appearance controls without changing saved settings
unless desired. Empty observations are not an all-clear.
