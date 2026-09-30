# 0.31.1 — BM report classification maintenance

Release candidate; not yet published.

## Runtime change

BM reports explicitly describing a burning `melléképület` (outbuilding), including
`melléképületben`, can now be labelled as local-asset fire candidates. The optional
landscape-focused BM card therefore hides clear outbuilding-only reports in its
default view; **All reports** still shows them. Reports mentioning vegetation as
well remain mixed, and negated or truncated inputs remain unknown and visible.
The original report text and stored history are preserved. These labels remain
textual clues, not official classifications or confirmation of fire extent.

## Offline research

Reviewed Makó word forms and Budapest direction-reference context improve the
offline place-name reviewer. They do not enable BM map markers, automatic
geolocation, new data sources or network requests in Home Assistant.

## Update

Update the integration through HACS, then restart Home Assistant when convenient.
No separate dashboard JavaScript replacement is needed from 0.31.0. Existing
entities, settings and history are retained; no storage reset is required.

## Validation

All 64 offline BM regression tests pass locally, including outbuilding-only,
mixed vegetation/building, negated and truncated input cases. Release-candidate
CI must also pass before publication. No production installation or live
acceptance check is claimed for this candidate.
