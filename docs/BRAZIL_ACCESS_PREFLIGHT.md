# Brazil INPE Queimadas preflight — 2026-09-30

Offline event inspection implemented. No HA provider, account or scheduled polling.

## Product distinction

https://data.inpe.br/queimadas/dados-abertos/ lists active-fire CSV/KML products
and separate Eventos de Fogo KML/GPKG products. The latter are explicitly
provisional and under validation. They are satellite-derived event products,
not ground-confirmed emergency-service incident reports.
https://data.inpe.br/queimadas/portal/evento-fogo/ explains hourly publication
with events processed through the previous day and active-front detections
updated within that product. Do not describe this as uniformly real-time data.

Before adding active-fire records, assess overlap with existing FIRMS/GOES
observations and preserve provenance; a second distributor does not constitute
independent confirmation of a fire. Derived event area and spread estimates
must remain provider estimates, not verified boundaries.

## Product licence and implementation requirements

Queimadas program data are subject to **CC BY-SA 4.0**. This scope is specific
to Queimadas; it is not a licence for all material hosted by BIG/INPE, Copernicus
imagery or Brazil Data Cube products. Do not transfer TerraBrasilis AMS's
separate CC BY-NC-SA wording to this product.

Implementation must retain INPE / Programa Queimadas attribution, a source link,
the [licence link](https://creativecommons.org/licenses/by-sa/4.0/) and notices
of transformations. Publicly shared adaptations must satisfy ShareAlike,
including applicable database rights. Processing software does not automatically
inherit the data licence. Keep original provenance when combining observations
from other distributors. A public data licence does not establish request quotas
or guarantee availability of an endpoint.

## Remaining runtime requirements

Verify the exact export scope, stable event identity across snapshots, source
timezone, collection transitions and supported polling/caching behaviour.
Do not infer extinguishment from disappearance or from the observation collection.

## Scope decision — 2026-09-25

Prioritize evaluating Eventos de Fogo as a separately labelled derived product,
not importing all INPE hotspot records into existing counters. Potential added
value: provider-estimated area, event duration and active-front context. This is
a design assessment, not measured improvement. The provisional maturity and
mixed publication/observation time semantics must remain visible to users.


## Offline KML event inspection

`tools/source_research/inpe_events.py` reads supplied UTF-8 KML with byte, node,
depth and event limits. It rejects entity declarations, network-linked feeds,
duplicate event identifiers, malformed coordinates and unsupported empty feeds.
It follows no embedded image/style links and renders no upstream HTML.

One record is emitted per event folder using its direct representative point.
Nested front/detection points are not additional events. Polygon presence is
recorded only; the inspector neither validates polygon boundaries nor treats the
representative point as a measured fire perimeter. Descriptions and provider
categories are retained verbatim; timestamps remain unresolved, with no invented
UTC conversion. Cross-snapshot ID stability is not established.

A 2026-09-30 sample from the official download page's active-event endpoint
contained 27,703,171 bytes and 3,732 unique event folders, each with a representative
point and polygon. Categories: 1,613 Nova Queima Isolada, 735 Possível início de
incêndio, 1,065 Incêndio, 319 Atividades Antrópicas. These are sampled provider
classifications, not field-confirmed incident status or current counts.

The observation directory advertised a 43 MB KML, exceeding the initial 32 MiB
inspection limit. It was not downloaded. An efficient distribution strategy and
measured resource limits are needed before enabling periodic HA retrieval.
No source snapshots are bundled in the repository; tests use synthetic records.

## Viewer JSON route and unresolved completeness

The official event page imports `pages/evento-fogo/js/config.js` under
`/queimadas/evento-fogo/`. It identifies
`https://data.inpe.br/queimadas/portal/api/eventos/centroides` as the representative
point endpoint; `mapa-eventos.js` loads details through `eventos/{id}` below the
same API base. Discovery in viewer code is not a third-party stability guarantee.

`inpe_centroids.py` validates the bounded GeoJSON envelope, unique integer IDs,
finite point coordinates and optional nonnegative area/duration fields. It
retains original category/status labels and unknown future labels, rejects
unsupported paging/CRS and empty inventories, and does not infer observation
or publication times. `inpe_fetch.py` is a one-shot explicit research request:
fixed HTTPS endpoint, no custom coordinates, redirects or retries, 8 MiB bound,
30-second socket timeout (not an absolute wall-clock deadline). No scheduler,
cache replacement, history reconciliation or HA entity activation is provided.

A 2026-09-30 sample contained 6,411 records in 2,925,140 bytes. Provider status
counts were 5,120 Observação, 555 Ativo and 736 Nova frente isolada. The official
formatter displays Nova frente isolada as Ativo; the inspector preserves the raw
label. Observação must not be translated as extinguished or controlled.

Comparison with the earlier KML sample found 1,291 shared IDs, no category
mismatches among them, 2,441 KML-only IDs and 5,120 API-only IDs (all Observação).
Different retrieval/publication times mean this is not proof of an upstream
bug. However, a sampled KML-only record remained directly queryable through the
detail endpoint with Nova frente isolada status. Thus the smaller list cannot
yet be assumed to be a complete replacement for the active KML export.

Detail date fields `data_min` and `data_max` are calendar-date strings;
`data_ultimo_foco` is a timestamp without an explicit offset. The methodological
paper discusses UTC processing days, but this does not alone establish the
serialization contract of these specific API fields. HTTP Date is a response
time, not observation time. Do not infer extinction from `data_max`.

Before production, establish list selection/completeness, pagination or record
caps, update/publication metadata, exact timestamp timezone, ID reuse/merge
semantics and suitable external-client request frequency. These are technical
source-contract requirements, independent of the confirmed data reuse licence.

## State-scoped follow-up

Further inspection resolves the sampled KML discrepancy: the full
`/queimadas/portal/api/eventos/mapa/eventos` response contained 17,102 unique
records, with exactly the same 3,732 active/new-front IDs as the active KML.
The remaining 13,370 were labelled Observação. The smaller national centroid
list is therefore not interchangeable with the full event inventory.

The official `pages/evento-fogo/js/centroides.js` uses `?uf=AC`-style requests.
Two state-scoped samples matched the full map's `estados` membership exactly:
Acre 1,694 records (763,043 bytes), Minas Gerais 1,560 (677,271 bytes).
For both states, the intersection with the smaller national centroid list was
exactly the subset with nonempty `regioes`. All 6,411 national centroid records
had this regional association. This strongly supports a scope filter, not random
loss; it does not prove server implementation or future completeness.

`inpe_snapshot.py` collects up to three explicitly selected states in a research
cycle, requiring returned `estados` membership. Identical cross-state duplicates
are retained once; conflicting duplicates or a failed request abort the cycle.
This research bound is not an INPE quota. The cycle has no scheduled polling,
persistence or HA activation. A parsed response never becomes a completeness
claim. Retrieval time is kept separate from unknown observation time.

The plain-data report includes INPE attribution, the product source link,
CC BY-SA 4.0, transformations and provisional status. It preserves raw categories
and statuses; Observação is not relabelled controlled/extinguished. Coordinates
remain representative points, and areas remain provider estimates.

The [methodological paper](https://doi.org/10.3390/rs18040606) establishes UTC
processing days, event date spans and a distinct fusion lifecycle. The exact
unqualified API timestamp representation, public successor linkage and external
client frequency remain unverified. No merge lineage is invented and no history
is deleted. Future display may omit unresolved clock times and preserve dates.
