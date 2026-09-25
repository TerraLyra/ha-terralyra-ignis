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
