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
fields retain their source meaning; no alerts or inferred ignition/extinction times
are created. Optional map/calendar presentation is described below.

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
relevant authority's original advice.

## Optional calendar and map

The **NIFC official reports** calendar is disabled by default. Enable it separately
in the entity list. It shares the same initialized source owner as the diagnostic
sensor; the sensor does not have to remain enabled for the calendar to work.

Calendar entries use the exact source modification timestamp, with reported discovery
time as the fallback. Missing dates are omitted and counted in calendar attributes.
A one-second event is only a display marker, never an assertion of fire duration.
Events are timed rather than grouped as all-day events. The description distinguishes
source records from satellite observations and warns when a prior response is retained.
This is a view of the current response, not a persistent historical calendar archive.

Turn on **NIFC report map** (Hungarian: **NIFC jelentéstérkép**) to show report markers.
The switch initially starts off and restores your last on/off choice after restart.
Select the `terralyra_ignis_nifc_reports` geolocation source in a map card if the card
filters sources. Wildfire reports, prescribed-fire reports and complex containers
have distinct labels/icons. They are not new satellite detections or independent
active-fire totals.

Each source point is compared locally with every enabled monitored location. The
marker's distance refers to the nearest matching location, identified explicitly in
its attributes; it never falls back to Home. All matching locations remain listed.
Missing geometry produces no marker. Complex relationships are retained, not merged.

A maximum of 500 matching source records can be displayed. If more match, the map
shows no subset and the switch reports `display_limit_exceeded` plus the match count;
reduce the monitored area before retrying. Turning the switch off removes only the
current markers. A record disappearing from a later source response removes its
marker but does not establish that the fire ended. No recorder/incident-history purge
is performed. Other NIFC consumers continue independently when the map is turned off.
