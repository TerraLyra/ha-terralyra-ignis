# 0.29.0 — readable reports and selectable map layers

## Included

- Optional IGNIS report map card with readable Canada/NIFC report dialogs.
- Independent satellite, Canada and NIFC layer switches and 1/7/30-day filters
  based on source status/update time. Unknown or future timestamps stay visible.
- Report age, original source status, local distance reference and attribution.
- NIFC source-provided incident names and short descriptions (up to 80 characters).
  Missing, unrequested and supplied descriptions remain distinct. The Canadian
  CWFIF feed has no narrative description field; this is explicitly identified.
- Text rendered as plain text, restricted external links, no article-page scraping.

## Installation

Update the integration to 0.29.0 through HACS and restart Home Assistant for the
NIFC text fields. Existing locations, identities and recorded history are retained;
no reset or first-use reinitialization is needed.

The card is **a separate optional installation**: download `ignis-report-map.js`
from this release, copy it to `/config/www/ignis-report-map.js`, register/update
one JavaScript module resource `/local/ignis-report-map.js?v=0.29.0`, and reload
the browser. Use `type: custom:ignis-report-map` on a duplicate map card. Existing
map settings can be retained. See [complete card setup](REPORT_DETAILS_CARD.md).
Do not register the old and new card files simultaneously. HACS does not copy
this asset into `www` or modify dashboard resources automatically.

## Validation and limits

109 offline NIFC tests, 7 card model tests and isolated browser tests passed.
The feature passed the full HA, HACS, Hassfest and security CI checks. Map layer
switches and age filtering were also checked in live HA. NIFC text retrieval
still needs post-upgrade validation against live responses; fields may be empty.
Source update time is not ignition time or proof of current fire activity.

BM OKF geographic extraction, calendar-only source adapters and providers awaiting
permission are not included. Optimization remains paused. No history is deleted.
