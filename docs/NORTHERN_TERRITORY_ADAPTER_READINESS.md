# Northern Territory access preflight — 2026-09-20

Status: research only; no provider, polling, HA entities or calendar integration.

## Exact products and evidence

- [NT government guidance](https://nt.gov.au/emergency/bushfire/stay-informed)
  points users to SecureNT and the joint NT Fire and Rescue / Bushfires NT map.
- [Official map](https://www.pfes.nt.gov.au/incidentmap) presents a last-24-hours
  view. Initial HTML zero counters do not establish an empty live feed.
- [Map disclaimer](https://www.pfes.nt.gov.au/incidentmap/disclaimer.html) states
  approximate 10–15-minute updates and approximate incident positions. This is
  a publication cadence, not a permitted client polling interval or freshness SLA.
- [Map legend](https://www.pfes.nt.gov.au/incidentmap/about.html) distinguishes
  incidents, warnings and planned burns. Fire includes several fire types; Advice
  also covers non-fire incidents. Bushfire Closed can still involve burning within
  containment lines. Neither closure nor disappearance means an area is safe.
  These UI categories are not a verified machine-feed schema.
- [PFES copyright](https://pfes.nt.gov.au/node/849) describes a non-commercial
  reproduction exception and written consent for other uses. It directs consent
  requests to the Corporate Communications and Recognition Unit. The email on
  that page is explicitly given for logo requests; it is not established here as
  a developer-feed support address. Ask the unit to route the enquiry appropriately.

No product-specific developer grant, supported machine endpoint, rate limits or
redistribution contract was verified. Do not interpret this as proof that every
non-commercial use requires approval: clarify the proposed filtering, display and
caching scope. No live incident payload or private locations were downloaded.

## Separate open dataset: burn permits

The [NT open-data burn-permit catalogue](https://data.nt.gov.au/dataset/bushfires-nt-burn-permits)
lists CC BY 4.0 for permit-area polygons. A permit grants an opportunity to burn;
it does not confirm ignition or an active incident. The catalogue excludes prescribed
burns and permits within Emergency Response Areas. Its licence cannot be transferred
to the incident map. This product cannot fill the active-incident coverage gap.

## Next gates

1. Confirm the supported incident-feed product, applicable reuse terms, attribution,
   local HACS distribution, caching and request limits with the operator.
2. Obtain schema and permitted examples for identity, timestamps, categories,
   completeness, retention and closure. Keep warning areas separate from incidents.
3. Validate coordinate semantics and source times; do not assign a timezone merely
   from jurisdiction. Establish any provider-specific interpretation explicitly.
4. Only then develop the bounded adapter with synthetic tests and opt-in behavior.

A request draft is in [provider requests](PROVIDER_ACCESS_REQUEST_DRAFTS.md).
No request was sent by the assistant. Victoria remains pending; ACT stays experimental.
