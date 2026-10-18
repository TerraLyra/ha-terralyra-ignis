# 0.40.6 — More reliable location summaries

Background updates preserve keyboard focus on Sensor details when the same
entity/location binding remains selected. Incident counts still update, and
updates do not take focus from controls outside the summary.

Satellite receipt times now use the Home Assistant timezone, matching forecast
receipt times. The shared display formatter rejects timezone-less inputs instead
of assuming browser-local time. Invalid locale or timezone settings fall back to
an explicitly labelled UTC timestamp. Stored timestamps and freshness calculations
are unchanged.

## Validation

Implementation PRs #201–#203 each passed all 27 automated checks. The frontend
suite contains 48 passing unit tests. Browser coverage includes keyboard activation,
background updates, outside-focus preservation, Budapest/Los Angeles timezone
rendering and UTC fallback when HA timezone configuration is absent.
Invalid formatting settings and timezone-less display inputs have unit coverage.
The release candidate has not been installed on production Home Assistant.

## Update

Update through HACS, restart Home Assistant, then fully reload the browser or
Companion App frontend. No storage migration or dashboard configuration change is
required. Providers, notification settings, entity IDs and stored history are
unchanged. See [resource recovery](CARD_RESOURCES.md#later-updates-and-rollback)
if a manually registered card remains stale.

After updating, confirm both location summaries render and receipt times follow
the HA timezone. Keyboard users can focus Sensor details and verify normal Enter
activation; automated tests cover the background-update transition.
