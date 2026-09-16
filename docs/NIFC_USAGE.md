# NIFC / WFIGS source diagnostics

This optional US official-source adapter retrieves source records, not satellite
observations. Attribution: **NIFC / WFIGS / IRWIN**.
[Original source and terms](https://www.arcgis.com/home/item.html?id=4181a117dc9e43db8598533e29972015).

## Enable after installing a version containing the adapter

1. In the IGNIS integration's entity list, enable **NIFC source status** (Hungarian:
   **NIFC forrásállapot**). It is disabled by default. At least one monitored location
   must also be enabled. The query is nationwide and sends no Home/location coordinates.
2. For genuine first use, open **Developer tools → Actions**, select
   `terralyra_ignis.initialize_nifc`, select a loaded IGNIS entry, and confirm first use.
   An identified administrator must run it. All entries share this initialization.
   Do not use it after deleting existing NIFC storage or to reset a pause.
3. The enabled sensor requests data once initialized. Successful requests are separated
   by at least 15 minutes; service waits/failures may extend this. Manual entity updates
   cannot bypass the wait. With no enabled NIFC sensor there is no source polling.

Initialization alone does not enable a disabled sensor. An already-enabled sensor can
start automatically after initialization. No API key or additional account is needed
for the currently verified public endpoint.

## Interpret the result

- **Not requested:** first-use initialization, eligibility or a first request is pending.
  The `initialization_status` attribute distinguishes an initialization requirement.
- **Response available:** a validated response is retained; this does not say the
  underlying fire reports are newly observed or still burning.
- **Waiting:** no response is cached and a retry/cooldown is in effect.
- **Retained response:** a prior response remains after an unsuccessful refresh.
- **Review required:** storage, source schema/access or a persisted pause needs attention.

`source_record_count` counts source records, with wildfire, prescribed-fire and complex
categories separate. Complex parents and children can overlap. Never use their sum
as an independent active-fire count. Receipt age measures time since download;
`source_freshness` and national completeness remain unestablished. Discovery/modification
fields retain their source meaning; this diagnostic adapter creates no map/calendar
entities, alerts or inferred ignition/extinction times.

## Recovery

Read the entry's Repair notice and resolve the underlying source/storage issue first.
An administrator can then run `terralyra_ignis.recover_nifc` and explicitly confirm review.
Known cooldowns are retained, with at least 15 minutes before any new request.
Recovery cannot run while a storage operation remains pending. It never deletes history.

Missing/corrupt stores, an unknown legacy pause, or an unbounded server delay are refused.
Do not delete `.storage` files or rerun first-use initialization as a workaround. Restore
validated NIFC storage from a backup or investigate the source's retry requirement.
A hung disk operation must finish or the storage issue must be resolved before recovery.
Disabling the last NIFC entity cancels retrieval and stops the timer; an interrupted
request may leave a durable review pause, which is deliberate.

Persistent keys are `terralyra_ignis.nifc_cooldown` and
`terralyra_ignis.nifc_initialization`. They are separate from all incident/history stores.
This implementation does not migrate, expire or delete user incident history.

## Data and operational limits

The adapter verifies an object-ID inventory at both ends of the request and requires
exact coverage for each subset. It rejects partial/truncated, conflicting or oversized
results. Boundaries are 10,000 records, 10 MiB total and 60 seconds overall; a source
change during retrieval causes a failed attempt rather than an incomplete display.
It is not an atomic national snapshot or an emergency warning service. Follow the
relevant authority's original advice. Maps/calendars remain a separate planned stage.
