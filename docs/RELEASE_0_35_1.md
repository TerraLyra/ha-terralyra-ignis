# 0.35.1 — Small icons for location summaries

The optional location summary card now includes small icons for the location,
satellite event counts, radii, data sources, forecast and restriction sections.
All text labels remain visible; the icons are decorative and hidden from screen
readers. They do not indicate a verified fire or an official restriction.

Data collection, incident tracking, notifications, blueprints and history are unchanged.

## Upgrade

Update in HACS and restart Home Assistant at a suitable time, then fully reload
the browser or Companion App frontend. If the bundled resource URLs introduced
in 0.35.0 are already configured, no resource or dashboard changes are needed.
For older local resources, follow [the one-time resource migration](CARD_RESOURCES.md).
