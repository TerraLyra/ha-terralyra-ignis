# TasALERT feed preflight

Research only; no runtime provider, entities or calendar entries are enabled.

## Products and attribution

The supported products in scope are:

- https://alert.tas.gov.au/data/cap-au.xml
- https://alert.tas.gov.au/data/incidents-and-alerts.xml
- https://alert.tas.gov.au/data/incidents-and-messages.kml

Redistribution of these feeds is permitted under CC BY 4.0. Attribute TasALERT,
link the original product and https://creativecommons.org/licenses/by/4.0/,
and identify filtering or transformation. Preserve supplied attribution and
notices; do not imply endorsement. This scope does not automatically extend to
other products or linked pages. Permission correspondence is not part of this
repository.

## Single snapshot — 2026-10-12

All three requests returned HTTP 200. The CAP-named endpoint contained an
EDXL-DE 1.0 envelope, with no content objects or CAP alerts. Its distribution
clock was `2026-10-13T04:09:07+11:00`, equivalent to October 12 17:09:07 UTC.
The RSS 2.0 channel contained no items. Neither empty response establishes
absence of incidents: the KML response simultaneously contained 20 placemarks.

KML 2.2 snapshot:

- 14 `incident` records: 2 Bushfire, 11 Fuel Reduction Burn, 1 Structure Fire.
- 6 `burnt-area` records, separate from the incident records.
- Incident statuses: 12 Patrol, 2 Going. Preserve these source values.
- All 14 incidents had Point geometry; 17 placemarks had Polygon geometry.
  An individual placemark can contain both, nested in MultiGeometry.
- ExtendedData keys included created, changed, number, title, type, status,
  agency, address, feedType, url and burntArea.
- Observed created/changed timestamps carried `+00:00`. KML coordinates use
  longitude, latitude order. Never treat a polygon vertex as an incident point.

The CAP HTTP response advertised a ten-second cache lifetime and up to 86400
seconds stale-if-error. A cache header is not a permitted polling interval or a
freshness guarantee. HTTP receipt and Last-Modified do not date a fire.

## Implementation direction

Start with offline KML parsing. Keep original type, status, agency, ID, number,
created/changed clocks and source link. Treat created/changed as record clocks,
not proven ignition/extinction times. Require explicit offsets; do not guess.
Use incident Point geometry only for an initial point adapter. Retain the
existence of area geometry without manufacturing a centre or conflating a burnt
area with an active fire. Preserve IDs as strings; do not assume incident number
or placemark ID reuse rules from a single snapshot.

Keep Bushfire, Fuel Reduction Burn and Structure Fire distinct. Do not map
Patrol to extinguished, Going to a measured perimeter, or feed removal to
extinction. Unknown types/statuses require explicit handling rather than a
silent assumption. Do not combine CAP, RSS and KML as independent events.

## Remaining technical checks

- Synthetic parser tests: nested geometry, malformed/duplicate IDs, coordinate
  range and ordering, explicit winter/summer offsets, invalid or naive clocks,
  unknown types, missing fields, XML input bounds and unsafe source links.
- Compare later snapshots for identifier continuity and feed overlap, including
  an actual CAP content object and RSS item when available.
- Establish a conservative request policy with conditional retrieval and backoff;
  no polling interval is inferred from the license or cache lifetime.
- Validate update/removal behavior before production wiring. An empty feed or
  failed parse must not erase retained reports or claim the area is safe.

## Offline parser checkpoint

`tools/source_research/tasalert_kml.py` validates bounded UTF-8 KML without network
access. It rejects entity declarations, duplicate IDs/fields, unknown feed types,
unsafe source links, invalid points and offset-free supplied clocks. Unknown
incident statuses/types remain verbatim. Polygon-only burnt-area records remain
separate and receive no fabricated point. It does not implement retrieval,
persistence, lifecycle transitions or production entities.

Seven synthetic test cases pass, including winter/summer offsets and the two
explicit offsets for a repeated DST clock. The saved 2026-10-12 sample parsed as
14 incidents and six burnt-area records. This validates that snapshot's syntax,
not identifier lifetime, completeness or status semantics.
