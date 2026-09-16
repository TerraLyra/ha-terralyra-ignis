# NIFC runtime delivery status

Updated 2026-09-16. This supersedes the earlier chronological preparation checkpoints.
Scope: opt-in source diagnostics and verified nationwide source-record retrieval.
Map markers, calendars, alerts and independent active-fire totals are later work.

## Implemented

- Integration-owned normalization, shared HA HTTP session, bounded async retrieval.
- ID inventory before and after retrieval, exact ID coverage in each batch, duplicate
  IRWIN rejection. No partial result becomes available. This verifies the returned
  inventory, not an atomic snapshot or the existence of every fire in the country.
- One disabled-by-default diagnostic sensor per config entry. Enabled sensors share
  a single HA-wide task and cooldown. No enabled sensors or monitored locations means
  no source request. No user coordinates are sent to NIFC.
- A one-minute eligibility tick; successful requests are at least 15 minutes apart.
  Manual refresh joins this schedule. Backoff and Retry-After can only extend waits.
- Explicit first-use admin action with separate initialization ledger. Setup never
  initializes storage automatically. Missing established or corrupt state blocks.
- Guarded storage: 30-second caller bound, no cancellation of the underlying write
  merely to satisfy that bound. Outstanding tasks remain referenced and registered
  with HA; completion/exception is always observed. Timeout/cancellation latches a
  review requirement and prevents overlapping operations.
- Final listener unload or shutdown cancels the request task. It waits up to five
  seconds for completion, then leaves a still-pending operation owned and blocked;
  no unobserved task or replacement request is created. HA handles final process
  shutdown; power loss cannot be made equivalent to a completed disk write.
- Fixed, translated Repair diagnostics scoped to each enabled entry.
- Explicit admin recovery validates both stores, refuses pending writes and preserves
  disk plus in-memory wait bounds. A newly issued recoverable pause has a version-2
  checkpoint with a review wait bound. Recovery adds at least 15 minutes, retains
  cached response/history, and never requests immediately. Version-1 finite waits
  remain readable. Unknown legacy/unbounded pauses and corrupt/missing checkpoints
  cannot be reset; investigate or restore validated backup instead.

## Live verification

On 2026-09-16 around 20:00 UTC, the offset-based full query stopped at a response
without exceededTransferLimit. No partial result was accepted. A 500-ID subset
request subsequently returned HTTP 404; repeating the inventory strategy with
100-ID subsets succeeded: 523 records, 8 requests (two inventory plus six record
batches), 160,970 bytes. Both inventories agreed and every requested ID was returned.
No raw incident payload was persisted or committed for these probes.

Runtime uses 100 IDs per batch and at most 100 batches / 10,000 records, with unchanged
10 MiB total, 1 MiB response and 60-second overall bounds. The batch count accommodates
the smaller URLs rather than removing the record/byte/time limits. Oversized inventories,
missing records and malformed responses fail closed. A changing final inventory
requires a later retry, not partial success. This sample does not guarantee future
availability or source correctness.

Protocol reference: [Esri query documentation](https://developers.arcgis.com/rest/services-reference/enterprise/query-feature-service-layer/),
returnIdsOnly and objectIds subsets. Attribution: NIFC / WFIGS / IRWIN.

## User operation

See [NIFC usage and recovery](NIFC_USAGE.md). The adapter remains disabled by default.
Enabling the entity and explicit first-use initialization are separate choices.
No release or live HA installation is implied by merging this implementation.
Existing optimization remains paused. No incident history migration, purge, inferred
closure, advanced correlation or private intelligence code is part of this work.
