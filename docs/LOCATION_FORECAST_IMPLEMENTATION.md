# Per-location forecast implementation plan

Status: design only, based on the 0.31.1 code. No new requests, entities or
provider activation are introduced by this plan.

## Existing behavior

`fire_risk_coverage.py` computes geographic compatibility for monitored locations
and is consumed by diagnostics. It does not schedule forecasts. The operational
`FireRiskCoordinator` still reads `hass.config.latitude/longitude`, uses one
entry-level forecast radius, and persists one `fire_risk_map` cache. The optional
summary card verifies an explicit near-home binding; it is not a multi-location
forecast implementation.

## First increment: isolated request context

Introduce a validated immutable forecast context containing stable location ID,
provider/product ID, latitude, longitude and **forecast** radius. Do not reuse the
active-fire monitoring radius implicitly. Geographic compatibility must be checked
against the forecast radius actually requested, not the active-fire radius.

Initially adapt only the existing Home coordinator to this context with identical
coordinates, radius, request cadence and storage identity. This increment must not
start requests for other monitored locations. Unit tests must prove parity before
widening runtime scope.

## Subsequent increments

1. Add explicit forecast settings per eligible enabled location. Preserve the
   existing Home forecast radius. Additional locations require an explicit forecast
   radius; do not copy the active-fire radius silently. Disabled/uncovered locations
   must not schedule work or create permanently unavailable forecast entities.
2. Plan independent coordinator contexts and bounded request scheduling. Document
   maximum requests per refresh across the supported number of locations before
   enabling the fan-out. Keep current provider limits/backoff and avoid refreshing
   every location simultaneously on each restart.
3. Isolate cached maps by config entry, provider/product, location identity and
   exact request geometry. Cache import must validate coordinates, radius, date,
   bounds and expiry. A location moved or resized must not reuse another geometry's
   map. Keep the existing Home cache compatible; do not purge history or old storage
   as an upgrade shortcut.
4. Keep current Home entity unique IDs and entity IDs. New eligible locations use
   their stable IDs, never names or list positions. Duplicate display names must
   remain distinguishable. Remove neither existing Home history nor user dashboard
   bindings during migration. Disabled locations stop fetching independently.
5. Extend summary bindings only when a forecast explicitly identifies its location.
   Require matching identity and geometry, plus a valid current UTC product day.
   Distinguish observation/issuance time from retrieval time; unknown issuance stays
   unknown. Missing, stale or failed retrieval must not imply low danger.

FRMv3 remains the first implementation target. GWIS and other candidates require
separate product-specific access, schema and operational verification. The older
[provider research](FIRE_RISK_PROVIDER_RESEARCH.md) is a research record, not a
current licence clearance or a commitment to activate a provider.

## Required regression scenarios

- Home-only setup retains IDs, radius, cache fallback and request cadence.
- Two covered locations receive their own values, including when names match.
- A covered and an uncovered location do not share forecast results.
- Rename preserves identity; move/radius change invalidates incompatible cache.
- Disabled locations cause no retrieval; re-enabling cannot leak another context.
- One provider/location failure does not replace another result or manufacture zero.
- Restart and old Home storage preserve usable data without rewriting history.
- UTC date rollover, expired forecasts and receipt/issuance distinction remain valid.
- Request budget and response-size bounds hold at maximum supported location count.

Implementation, focused tests and candidate CI precede any release. Live deployment
must be validated separately; this plan makes no live acceptance claim.
