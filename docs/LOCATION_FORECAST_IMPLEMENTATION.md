# Per-location forecast implementation plan

Status: foundations implemented; per-location runtime activation remains pending.
The existing Home forecast remains operational. No additional location requests
or public entities have been enabled.

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

## Foundation progress

The Home request context is implemented and retains legacy radius fallback,
cache identity and cadence. Pure per-location settings/planning and scoped cache
envelopes are now implemented separately. They are not wired into config flow,
coordinator creation or public entities: an eligible plan is not a live forecast.
Missing, disabled and uncovered locations receive no request context. No settings
are inferred from a location name or its active-fire radius.

A scoped cache envelope checks exact context identity first; provider cache import
must still enforce payload bounds, validity date and age. These envelopes must not
replace the legacy Home cache format during migration.

### Retrieval cost before runtime expansion

The current client needs at most nine point samples to find today's valid pixel,
then nine future-day point requests: at most 18 point requests per successful
forecast plus one coordinator map request (19 total without a map cache hit).
An all-nodata result uses nine point requests. A current-day 404 can add one
capabilities request before aborting the refresh; future-day 404 is missing data.
These figures bound one coordinator refresh, not user-triggered camera requests,
retries, total hourly traffic or a provider-authorized polling allowance.

Ten additional locations plus legacy Home could therefore produce 209 requests
in one uncached successful refresh cycle. Runtime expansion must introduce shared
bounded scheduling/backoff and explicit opt-in before creating those coordinators.
No additional polling is enabled by the pure planner or these tests.

A shared opt-in request gate now serializes operations and spaces them by at least
one second after completion. Rate-limit or transient service errors pause peers
for the bounded 15–60 minute retry period without retrying the failed operation
inside the gate. This is a local policy, not an upstream quota. It is not wired
into existing Home retrieval. During a shared cooldown, peers receive a local scheduling deferral without
a network call or a long sleep inside the coordinator timeout. Bounded UTC
deadline import/export supports restart recovery; runtime orchestration must
still persist/restore that state and schedule deferred updates before activation.

### Durable request-gate foundation

`FireRiskClient` accepts an optional shared request gate. When supplied, it gates
every actual HTTP operation (point, capabilities and map), including errors,
while map cache hits require no request. Existing setup supplies no gate and
retains its current behavior.

`PersistentForecastRequestGate` restores a provider-labelled cooldown before its
first request and saves a new cooldown before releasing queued peers. A failed
load prevents traffic and can be retried; a failed/cancelled save remains dirty
and must succeed before another request. Malformed, wrong-provider or unsafe
future state fails closed; a valid expired deadline permits retrieval. No state
file is deleted, and legacy Home map storage is untouched.

The runtime owner must create exactly one gate and installation-wide FRMv3 store,
share it across entries and clients, and schedule local deferrals appropriately.
That owner, config flow and additional coordinators are still pending. These
classes alone neither create storage nor increase live request volume.

### Isolated location coordinator

`LocationFireRiskCoordinator` now owns an immutable FRMv3 context and a separate
client/map cache. Its storage key includes config entry and exact context hash;
changing coordinates/radius cannot import old geometry. Its returned value keeps
the requested context separate from the sampled forecast pixel. It never reads
HA Home coordinates and never raises the legacy Home repair issue.

Construction requires a persistent shared gate and supported FRMv3 centre. The
runtime owner must still supply an explicitly enabled plan, share the gate,
stagger startup, and unload/replace coordinators when location settings change.
No coordinator is constructed by integration setup yet; no new entity exists.
Local deferrals schedule a bounded retry without increasing provider failure
counts. An optional map failure preserves valid point data; a forecast failure
does not overwrite a peer's data. Cache write failure does not erase a received
forecast. Legacy Home storage and entity identities remain unchanged.

The coordinator rejects missing/old UTC product days before map retrieval and
checks again after map processing to cover midnight rollover. A received result
is not a permanent freshness guarantee: future entities/cards must also check
its product day when rendering retained coordinator data.

### Lifecycle foundation

`LocationForecastRuntime` builds coordinators only from explicit eligible plans.
Construction performs no storage/network I/O. `start()` is idempotent and staggers
initial refreshes into deterministic slots 30–314 seconds after startup (at most
ten locations); periodic updates remain coordinator-owned. HA's disabled-polling
preference also suppresses startup. The caller supplies one shared provider gate.

`close()` cancels delayed callbacks, owned listeners and ongoing requests, awaits
cancellation, and leaves all stores/history intact. A closed owner cannot restart;
configuration changes must close it before creating its replacement. Coordinators
now restore cache lazily before their first background refresh, retry failed
restores before network access, and cancel in-flight updates on shutdown.

Integration setup, explicit settings UI, installation-wide gate sharing with
legacy Home and public entities are still pending. The lifecycle class is not
instantiated by setup yet and does not activate additional polling by itself.
