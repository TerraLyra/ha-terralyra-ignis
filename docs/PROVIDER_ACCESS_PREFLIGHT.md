# Provider access preflight

Workflow adopted at the user's request on 2026-09-18. Apply before starting a new
provider or adding a materially different product to an existing provider.

1. Identify the exact product, operator and official access documentation. Separate
   incident points, warning areas, forecasts, imagery and derived fire detections.
2. Check access and reuse independently: registration/approval, product licence,
   attribution, permitted processing/display/redistribution, local HACS use versus
   commercial Cloud use, request limits, credentials and retention.
3. Record dated authoritative evidence and distinguish explicit requirements from
   unknowns. A public endpoint is not a licence; unknown terms are not proof that
   permission is required. A clear applicable open licence does not need a redundant
   individual permission request.
4. Tell the user immediately if registration, approval, advance notification or
   clarification is needed. Include the verified contact route and prepare a request
   before substantial adapter work. Do not send it without explicit authorization.
5. Continue independent work while external answers are pending: synthetic tests,
   offline validation and other providers with established access. Keep provider
   research separate from enabled runtime. Do not invent source semantics.
6. Before activation, verify that the returned terms cover the intended implementation.
   No shared developer credentials in a public integration. Update this record when
   the product, licence, endpoint or intended usage changes. Never store credentials
   or private correspondence in the public repository.

## Ahead-of-development queue — checked 2026-09-18

| Product | Access / permission status | User action or next check |
| --- | --- | --- |
| Victoria CFA-listed developer JSON | Product-specific developer conditions unresolved; offline research complete, runtime absent | [VicEmergency form](https://support.emergency.vic.gov.au/hc/en-gb/requests/new). The user confirmed submission on 2026-09-20; response and approval are pending. |
| WA DFES-066 Incident Points | Explicit SLIP registration and dataset approval; catalogue lists CC BY 4.0 plus EmergencyWA terms | User confirmed submission on 2026-09-21; response and approval pending. Contact **statepublicinfo@dfes.wa.gov.au**. Confirm public HACS/per-user authentication eligibility, including resource-level Government Use Only labels. |
| Tasmania TasALERT feeds | Explicit permission required; do not inherit legacy TFS feed terms | User confirmed sending the access request on 2026-09-21; response and approval pending. Contact: **info@alert.tas.gov.au**. |
| SA CFS / ESO feeds | Original SA CKAN package reports CC BY-NC-ND 4.0; the national mirror omits the licence | User confirmed submission on 2026-09-21; response and approval pending. Clarify local HACS use and current terms before implementation; commercial use needs separate permission. See [SA review](SOUTH_AUSTRALIA_ADAPTER_READINESS.md). |
| NT Fire Incident Map | Website reuse conditions do not establish a product-specific developer grant | Clarify supported feed and local HACS reuse before adapter work; see [NT review](NORTHERN_TERRITORY_ADAPTER_READINESS.md). |
| ACT Current Incidents | Explicit CC BY 4.0; no additional individual permission requirement found for that feed | Keep experimental pending timestamp evidence. CAP is a separate product. |
| JAXA Himawari WLF | Registration; current FAQ lists qualifying data from 2026-02-01 as commercially usable; research-data policy requires advance commercial-use notification | Product/date-specific clarification with JAXA; distinguish notification from permission and older data restrictions. |
| NOAA/AWS Himawari imagery | Open public access; attribution and modification/endorsement conditions | No individual permission requirement stated for this distribution. This does not license a separate provider's WLF product. |

Official evidence:
- [WA DFES-066 catalogue](https://catalogue.data.wa.gov.au/dataset/dfes-emergencywa-incident-points-dfes-066)
  states the SLIP/group/dataset request sequence and normally five business days for
  review. This is a published target, not an IGNIS guarantee.
- [TasALERT data-feed FAQ](https://alert.tas.gov.au/about-app) explicitly gives the
  permission requirement and email. TFS warnings/incidents are now published there.
- [CFS copyright](https://cfs.sa.gov.au/home/copyright/) and
  [disclaimer](https://www.cfs.sa.gov.au/home/disclaimer/) distinguish site content
  and linked-site conditions; a site-wide grant is not assumed to cover every ESO feed.
- [JAXA FAQ](https://www.eorc.jaxa.jp/ptree/faq.html),
  [research-data policy](https://earth.jaxa.jp/en/data/policy/index.html),
  [older P-Tree terms](https://www.eorc.jaxa.jp/ptree/terms.html): wording differs;
  resolve the exact product/date/use before activation.
- [NOAA/AWS Himawari registry](https://registry.opendata.aws/noaa-himawari/).

See [ready-to-send WA and Tasmania requests](PROVIDER_ACCESS_REQUEST_DRAFTS.md).
No request has been sent by the assistant; no access approval is asserted here.

## Portugal — checked 2026-09-25

ANEPC's ProCiv catalogue explicitly lists CC BY 4.0, but the current viewer and
legacy resource link differ. Verify the current supported endpoint and licence
mapping before implementation; no individual permission requirement is asserted.
Official evidence, open questions and an unsent enquiry draft are recorded in
[Portugal preflight](PORTUGAL_ACCESS_PREFLIGHT.md).

2026-09-25 update: the user confirmed sending the Portugal enquiry; response
pending. [Brazil INPE preflight](BRAZIL_ACCESS_PREFLIGHT.md) identifies satellite
product overlap and BIG commercial-authorization wording; product-specific
applicability to Queimadas exports remains to be clarified before runtime work.

2026-09-25: user confirmed sending the Brazil INPE enquiry as well. Both Portugal
and Brazil now await replies; neither submission constitutes approval.

## Spain — Castilla y León, checked 2026-09-25

The official regional daily wildfire-report dataset explicitly specifies
CC BY 4.0 and has a working anonymous API. Bounded offline research is complete;
no general individual permission requirement was identified. Incident identity,
coordinate meaning, timestamp semantics and stable snapshot retrieval remain
open before runtime work. See [Spain research](SPAIN_ACCESS_PREFLIGHT.md).

2026-09-25: user confirmed sending the Castilla y León technical enquiry via
the official contact form. Reply pending; do not send a duplicate.

## France and Germany — initial triage, 2026-09-25

User authorized research of both countries. Separate incident reports, public
warnings, historical statistics and forecast danger indices. No runtime work.

France: BDIFF is the official national historical incident database. Current
incident timeliness, machine access and product licence still need verification.
https://bdiff.agriculture.gouv.fr/
https://bdiff.agriculture.gouv.fr/aide/generalites
Météo-France's Météo des Forêts API is a different product: departmental fire
danger for J+1/J+2, with account-required access (catalogue: 100 requests/min).
It is not an active-fire feed. Verify product terms and user-owned credentials
before implementation; contact listed by publisher: contact.api@meteo.fr.
https://www.data.gouv.fr/dataservices/api-meteo-des-forets

Germany: BBK MoWaS/NINA is a candidate for official large-fire/smoke warnings,
not a complete inventory of fires. BBK explicitly requires a multiplier agreement
for direct MoWaS connection. Whether this applies to local consumption of public
RSS/API must be established separately; do not infer either permission or a
blanket prohibition from the direct-connection rule. No enquiry sent yet.
https://www.bbk.bund.de/DE/Warnung-Vorsorge/Warnung-in-Deutschland/Warnmultiplikatoren/warnmultiplikatoren_node.html
https://www.bbk.bund.de/DE/Warnung-Vorsorge/Warnung-in-Deutschland/MoWaS/mowas_node.html
DWD WBI is a separate fire-danger forecast candidate, not incident evidence.
Check the operational product, freshness, spatial scope and applicable terms;
the CDC derived index archive alone does not establish a live forecast endpoint.
https://opendata.dwd.de/climate_environment/CDC/derived_germany/fire_danger_index/woodland/

Priority: inspect public-warning access terms for Germany and official incident
publication options for France, then evaluate the two danger-index products
as supplementary layers. A public catalogue listing alone is not evidence of
official authorship or permission for every hosted dataset.

## France/Germany follow-up — 2026-09-25

BDIFF's official search help describes annual campaigns, partial/unvalidated
records and retrospective corrections. Its detail map centres on the commune
of fire origin and displays its boundary: do not mistake that map centre for
an ignition point. CSV exports include legal and definitions PDFs. General help
states end-of-season validation takes place December–April of the following year;
this alone does not prove that no provisional current-year records exist.
No live publication latency or supported incident API was established.
https://bdiff.agriculture.gouv.fr/aide/recherche
https://bdiff.agriculture.gouv.fr/aide/generalites

The published BDIFF legal notice requires information integrity, explicit source
attribution and restricted reproduction wording, and excludes commercial or
advertising uses. Do not assign an open licence based solely on government
ownership. Product-specific alternative terms would need evidence. Deprioritize
BDIFF for the current live incident goal; retain as a historical research lead.
https://bdiff.agriculture.gouv.fr/mentions-legales

BBK's served NINA legal notice explicitly allows redistribution of federal
official warnings unchanged with attribution under its cited UrhG provision.
It separately addresses third-party warnings (Länder, municipalities, DWD etc.).
This is positive evidence, but not a verified blanket grant for every payload,
API polling or asset. Non-warning text/images remain permission-restricted.
The served notice states 20 March 2020 and app release information from 2023;
record that age instead of assuming a newly issued policy.
https://warnung.bund.de/api/appdata/gsb/html/DE/app/impressum.html

BBK publicly advertises per-location RSS warning subscriptions. Distinguish
these warning feeds from BBK's institutional news RSS. Public feed consumption
is not automatically the same as a direct MoWaS multiplier connection.
Next: verify supported public RSS/API access, polling and regional warning reuse
with the documented NINA contact nina@bbk.bund.de if not resolved in published
terms. No German or French enquiry has been sent or confirmed by the user.
https://www.bbk.bund.de/DE/Warnung-Vorsorge/Warn-App-NINA/warn-app-nina_node.html

Priority remains Germany official warning feeds; France needs an operational
national or regional official incident source before an adapter is proposed.
No production entities, credentials, data downloads or HA configuration changed
in this documentation step (only public documentation was fetched).

## FR-Alert candidate — 2026-09-25

A better operational-warning lead than BDIFF is the official FR-Alert site:
https://www.fr-alert.gouv.fr/les-alertes
Its legal notice explicitly assigns Etalab 2.0 to site content except separately
identified third-party intellectual property, requiring source, last-update date
and no misleading presentation. A blanket permission request for covered content
is therefore not justified. Technical access remains a separate question.
https://fr-alert.gouv.fr/mentions-legales

A bounded retrieval of the alert-list HTML exceeded both 1 MiB and a subsequent
4 MiB cap. The saved prefix is incomplete and must never be ingested as a complete
snapshot. It contains individual alert links, forest-fire and industrial-fire
labels, and an exercise filter. This establishes useful candidate structure,
not verified exercise flags on individual records, current active status, archive
completeness, latency or a supported API. No detail timestamps are inferred from
numeric URL components. Alert coverage is not a census of all forest fires.

Next: find a supported bounded feed or pagination and validate individual alert
status, updates/cancellations, exercise markers, dates with offsets and warning
area geometry. A warning area must not be rendered as a precise ignition point.
Avoid polling the full multi-megabyte archive in each user's installation.
No FR-Alert enquiry sent; no provider enabled.

Germany follow-up: official BBK pages continue to advertise per-location RSS,
but no publisher API contract/polling policy was found in this bounded search.
The community bundesAPI/bund.dev documentation is not itself BBK authorization.
Public website entry and help route require JavaScript; this is not an access
denial or evidence that API access is prohibited. Supported access and Länder/
municipal warning reuse remain questions for nina@bbk.bund.de.

2026-09-28: user confirmed submitting the FR-Alert technical enquiry via the
official contact form. Await reply; do not duplicate the request. See
[France research](FRANCE_ACCESS_PREFLIGHT.md).

2026-09-28: Germany review identified existing core NINA integration and its
detail action. Assess IGNIS-specific report presentation before duplicating
retrieval. Publisher clarification remains unsent. See
[Germany preflight](GERMANY_ACCESS_PREFLIGHT.md).

2026-09-28: user confirmed the German BBK/NINA enquiry has been sent. No replies
have arrived to any provider enquiries according to the user's latest update.
All pending technical/access questions remain open; submission is not approval.
