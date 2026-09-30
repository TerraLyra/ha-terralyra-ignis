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
