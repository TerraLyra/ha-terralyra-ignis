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
caching/redistribution and attribution. No message has been sent to INPE.

## Scope decision and enquiry draft — 2026-09-25

Prioritize evaluating Eventos de Fogo as a separately labelled derived product,
not importing all INPE hotspot records into existing counters. Potential added
value: provider-estimated area, event duration and active-front context. This is
a design assessment, not measured improvement. The provisional maturity and
mixed publication/observation time semantics must remain visible to users.

No product-specific licence resolving the BIG terms was identified in the
Queimadas FAQ/download documentation reviewed. Papers' CC BY licences do not
license their underlying datasets. Do not transfer another INPE product's terms.

Unsent draft to the support route published in BIG terms (data.suporte@inpe.br):

Subject: Queimadas exports: applicable terms and local Home Assistant use

Hello INPE team,

We are developing TerraLyra IGNIS, an open-source Home Assistant integration.
We are evaluating the Queimadas active-fire CSV/KML exports and, separately,
the provisional Eventos de Fogo KML/GPKG products published at
https://data.inpe.br/queimadas/dados-abertos/.

Could you confirm which terms apply to these specific exports? The Queimadas
FAQ describes free access, while the BIG terms require registration and prior
express authorization for commercial/economic platform use.

Our immediate proposal is direct retrieval on each user's Home Assistant
installation, local filtering and caching, and attributed display in a publicly
distributed HACS integration. Does this require registration or permission?
Please specify attribution, recommended request intervals, caching/retention
limits and any restrictions on displaying processed excerpts or geometry.

We would label Eventos de Fogo as provisional satellite-derived estimates,
retain their source and time semantics, and not present them as independent
emergency-service confirmation. A future commercial Cloud service would be a
separate use case; please indicate its authorization process separately.

Please also point us to the supported download routes and documentation for
stable event IDs, revisions, timestamps/timezones and active/observation status.

Kind regards,
Janos Bali
TerraLyra

## Submission status

2026-09-25: the user confirmed sending the INPE enquiry. Awaiting response;
no permission, registration exemption or product-specific licence confirmation
is inferred. Earlier draft text is retained as preparation history, not the
current submission status. No runtime provider is enabled.
