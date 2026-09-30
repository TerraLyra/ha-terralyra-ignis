# Brazil INPE Queimadas preflight — 2026-09-25

Research only. No data adapter, account, download polling or production change.

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

## Access and reuse gates

https://data.inpe.br/queimadas/faq/ describes free access and citation guidance.
Free access alone does not establish unrestricted commercial reuse.
https://data.inpe.br/dados/termo-de-uso-e-politica-de-privacidade/
(BIG terms, updated 2025-08-29) requires registration for its services and
prior express INPE authorization for commercial/economic platform use. It
requires source citation and identifies data.suporte@inpe.br as support.
The exact application of BIG registration and terms to anonymously published
Queimadas CSV/KML and event exports remains unverified; do not impose it as
an established product-specific requirement or infer an exemption.

The TerraBrasilis AMS page has its own CC BY-NC-SA 4.0 wording; that separate
product licence must not be transferred to all INPE Queimadas products.

## Next step

Clarify the precise Queimadas product terms and supported distribution route
with BIG support before substantial adapter work. Separate local public HACS
retrieval from future commercial Cloud use. Obtain polling guidance, permitted
caching/redistribution and attribution.

## Scope decision — 2026-09-25

Prioritize evaluating Eventos de Fogo as a separately labelled derived product,
not importing all INPE hotspot records into existing counters. Potential added
value: provider-estimated area, event duration and active-front context. This is
a design assessment, not measured improvement. The provisional maturity and
mixed publication/observation time semantics must remain visible to users.

No product-specific licence resolving the BIG terms was identified in the
Queimadas FAQ/download documentation reviewed. Papers' CC BY licences do not
license their underlying datasets. Do not transfer another INPE product's terms.
