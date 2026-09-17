# Victoria developer feed readiness — 2026-09-16

Status: reachable research candidate; not enabled or implemented.

## Evidence

The [CFA developer-feed page](https://www.cfa.vic.gov.au/rss-feeds) publishes
the JSON endpoint and identifies EMV as the developer-access manager. A bounded
direct request succeeded. [Metadata](VICTORIA_SAMPLE_METADATA_2026_09_16.json)
records the size, hash, field inventory and aggregate observations; raw incidents
are not included as repository fixtures.

Four records included one Fire, two Other and one Accident / Rescue category.
All had point coordinates and unique incident numbers in this sample. Millisecond
epoch update values matched the corresponding local update strings when converted
to Australia/Melbourne. This is evidence for a time interpretation, not a provider
guarantee. Planned burns, warning polygons, daylight-saving transitions, updates
across multiple snapshots and identifier reuse were not observed.

## Access condition still unresolved

The production [VicEmergency terms](https://emergency.vic.gov.au/about-this-site/terms-of-use)
restrict copying and adaptation of application content and require prior written
permission for broader reuse. They do not establish a developer-feed licence.
The separate [copyright page](https://emergency.vic.gov.au/about-this-site/copyright)
also references applicable terms and third-party restrictions. Generic Victorian
government open-data licensing must not be substituted for this product's terms.

Needed evidence: an EMV developer agreement or official product-specific licence
covering fetching, filtering and display in a distributed Home Assistant integration,
with attribution, polling limits and retention conditions. Commercial Cloud reuse
requires its own scope check. No enquiry was sent and no agreement was accepted.

## Adapter acceptance criteria once access is resolved

1. Validate the `results` envelope and bound bytes, records and nesting. Malformed
   data must not become a successful empty feed.
2. Establish a documented fire-category mapping. Preserve raw categories and count
   excluded or unknown records. Do not turn rescue/accident records into wildfires.
3. Check ID stability across snapshots before relying on `incidentNo` for identity.
4. Verify timestamp semantics, including DST ambiguity and conflicts between epoch
   and local strings. Receipt time must never substitute for event time.
5. Treat coordinates as reported incident locations, not fire extent. Preserve
   source status; `Safe` must not become a general all-clear for a monitored area.
6. Obtain planned-burn examples before supporting that subtype. Do not infer warning
   areas from this incident-point sample or invent thermal observations.
7. Use synthetic fixtures for missing/invalid fields, mixed categories, duplicate
   IDs and date conflicts; add licensed provider fixtures only when permitted.
8. Keep the calendar opt-in, preserve existing identities/history, apply bounded
   requests and stale-data labels, and test local relevance against each monitored
   location rather than always comparing with Home.

This review changes documentation only. Victoria remains a priority, but deployment
depends on the outstanding product-specific conditions and semantic checks above.

## Research continuation after ACT — 2026-09-16 21:06 UTC

Rechecked the official CFA feed page: RSS retains personal/non-commercial and
unmodified-content restrictions, while the separate developer section delegates
access to EMV and lists XML/JSON endpoints. These are distinct products; the RSS
conditions neither grant nor conclusively deny the required developer permission.
Targeted official-site searches did not locate a product-specific developer licence.

A new bounded read of the documented JSON endpoint returned HTTP 200, 1,417 bytes,
application/json; charset=UTF-8, no redirect, HTTP Date 21:06:53 GMT. The root is a
JSON object with a `results` key. This probe establishes availability/envelope only,
not empty-feed semantics, completeness or reuse permission; no raw incidents saved.
Next work is a synthetic envelope/time inspector and verification of EMV developer
conditions before distribution of an operational adapter. ACT uncertainty does not
block that research. WA catalogue also continues to mark incident products as
subject to approval; it is not an unrestricted fallback for Victoria.

## Offline envelope inspector — 2026-09-17

`tools/source_research/victoria_feed.py` now validates the observed `results` array
inside a bounded UTF-8 JSON response. It rejects duplicate keys, non-finite numbers,
malformed/extra envelopes, oversized arrays, nested or empty records and incomplete
responses. Unknown scalar fields and original values are retained without category,
identity, timezone or freshness inference. Empty valid arrays remain distinct from
failures. Diagnostic summaries expose only fixed labels and record counts. It has
no network, persistence or production HA imports. Six synthetic tests bring the
complete offline source suite to 163 passing tests.

A newly located [official support article](https://support.emergency.vic.gov.au/hc/en-gb/articles/235717508-How-do-I-access-the-VicEmergency-data-feed)
says access was not public and invites expressions of interest. It was last updated
6 February 2019, so it cannot establish the current status of the separately listed,
reachable CFA developer endpoint. Its linked EMV emergency-data page returned 403
to the research browser; no access restriction was bypassed. The current CFA page
still lists developer XML/JSON links. These conflicting/dated descriptions leave
product-specific permission unresolved, rather than proving access is prohibited.

Next evidence needed: current EMV developer conditions covering local fetching,
filtering/display, attribution, polling and retention. A request could reference the
exact CFA-listed getIncidentJSON endpoint and distinguish public local HACS use from
any future commercial Cloud product. No enquiry was sent, agreement accepted, live
HA entity created or release published. ACT remains experimental and unchanged.
