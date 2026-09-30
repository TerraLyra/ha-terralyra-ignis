# Per-location FRMv3 forecasts

Status: implemented on the development branch; candidate validation precedes
release. Live deployment has not been validated. Other forecast providers are
not activated by this feature.

## Explicit settings and identity

The integration's monitored-location menu includes **Location fire-risk forecast**.
Select a location, enable forecasting explicitly and enter a separate 1–500 km
forecast radius. There is no default copied from satellite monitoring. Disabled
locations and centres outside FRMv3 European coverage cannot be enabled. Existing
stored settings for temporarily disabled/uncovered locations remain inert.
Deleting a location removes its forecast options, not its history or map stores.

Settings are a bounded list keyed by stable location ID. Renaming a location does
not change its sensor identity; duplicate display names receive an ID suffix.
Changing geometry replaces the coordinator on options reload and changes its map
cache key. Main options updates preserve per-location settings.

Legacy Home retains its existing sensor IDs, radius, map store and normal update
interval. Enabling a monitored location at Home coordinates is an explicit,
additional forecast, not an implicit migration of those legacy entities.

## Shared request pacing and recovery

All FRMv3 clients, including legacy Home and camera requests, use one persistent
provider gate per HA installation. Actual HTTP operations are serialized with at
least one second spacing after completion. This changes intra-refresh request
pacing, not the legacy Home polling interval. No provider-authorized quota is
implied by this conservative local policy.

Rate-limit/transient errors pause peers for a bounded 15–60 minutes. The UTC
cooldown is restored before requests and persisted before queued peers resume.
Failed loads or dirty saves block traffic until they succeed. Local deferrals
are not counted as new provider failures and do not raise a Home outage repair.
Malformed persisted state fails closed. State/history is never deleted to recover.

A forecast uses at most 18 point requests (nine current-day sample attempts,
then nine future days), plus one uncached map. An all-nodata result uses nine
point requests. A current-day 404 can add a capabilities request before aborting.
Ten additional locations plus Home can therefore make 209 requests in a successful
uncached refresh cycle. This is not an hourly allowance: camera requests, retries
and other config entries are separate but share the same gate.

## Lifecycle and cache

Only explicitly enabled eligible locations get coordinators and new sensors.
Initial updates are staggered into deterministic 30–314 second slots, at most ten
locations per entry. Normal refreshes use a roughly twelve-hour interval.
HA's disabled-polling preference suppresses location startup and periodic polling.
Options reload/unload cancels timers, listeners and in-flight requests before a
replacement owner starts. No existing cache/history is removed.

Each immutable context contains stable location ID, provider/product, coordinates
and forecast radius. A separate client cache is scoped by config entry plus exact
context hash. Cache imports check context, bounding box, provider validity and age.
Background refresh restores the cache lazily once; failed restores are retried
before network access. Optional map failure preserves valid point data.

## Presentation and time semantics

The location sensor exposes the requested location separately from the sampled
pixel, which can differ when a nearby valid pixel is used. Its unique ID is based
on entry and stable location ID. A current UTC product day and matching context
are required; failed or stale data is unavailable, never low risk or zero.
Midnight updates invalidate yesterday's displayed data even without a new fetch.

`generated_at` means successful retrieval time, not model issuance. Unknown model
issuance is not inferred. The summary card supports explicit location ID,
coordinates and forecast-radius binding; a geometry mismatch suppresses the risk.
Legacy near-home card bindings remain supported. See
[location summary configuration](LOCATION_SUMMARY_CARD.md).

## Validation and remaining work

Regression coverage includes inert settings, separate radii, cache isolation,
shared cooldown recovery, deterministic startup, cancellation, main-options
preservation, location identity, current product dates, UTC midnight, sensor
availability and card binding. No real provider traffic is required by tests.

Release preparation and live acceptance remain separate: verify new optional
entities after installing a reviewed release, initial delay, a valid current-day
result, disable/re-enable and retained legacy Home history. No automatic HA
restart or dashboard edit is part of this implementation.
