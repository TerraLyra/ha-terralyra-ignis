# Portugal ANEPC access preflight — 2026-09-25

Status: research only; no runtime provider or HA change. No enquiry sent.

## Verified official evidence

- https://dados.gov.pt/en/datasets/prociv-ocorrencias-em-aberto
  identifies ANEPC as producer, lists CC BY 4.0 and shows last update
  2021-06-24. Description covers ongoing mainland Portugal civil-protection
  operations, including situations in resolution. It is not a wildfire-only
  dataset and absence does not establish an all-clear.
- https://prociv.gov.pt/pt/home/ links its current OCORRÊNCIAS view to
  https://prociv-portal.geomai.mai.gov.pt/arcgis/apps/experiencebuilder/experience/?id=29e83f11f7a34339b35364e483e3846f
  This establishes the current viewer's official provenance, not an API contract.
- https://prociv.gov.pt/pt/contactos/ publishes geral@prociv.pt as the
  general institutional contact. It is not a verified developer support inbox;
  ask for forwarding to the responsible data team.

## Distinguish reuse from access

The catalogue explicitly states an open licence. Do not assert that individual
permission is mandatory for that licensed dataset. However, the legacy resource
link and current viewer differ, and this review has not established the exact
current machine-readable product covered by that licence. Public reachability
alone does not resolve that mapping, request limits or authentication.

Do not substitute Fogos/other third-party redistribution endpoints for an ANEPC
source without a separate review. Do not infer Madeira/Azores coverage from the
mainland description.

## Remaining technical evidence before adapter implementation

Identify the supported endpoint and licence linkage; verify authentication,
polling limits, caching and retention. Obtain incident identifiers/reuse policy,
category codes (rural/vegetation versus building/vehicle fires), coordinate CRS
and precision, timestamp meanings and explicit timezone/DST semantics, paging
or truncation indicators, and disappearance/closure rules. Keep update times
separate from incident onset and do not infer burned area from point geometry.

## Draft enquiry (not sent)

Subject: ANEPC incident data — supported endpoint and reuse documentation

Hello ANEPC team,

We are developing TerraLyra IGNIS, an open-source Home Assistant integration.
The official dados.gov.pt catalogue lists “ProCiv - Ocorrências em aberto” under
CC BY 4.0, while your current website links to a newer incident map.

Could you direct us to the supported machine-readable endpoint for this product
and confirm whether the catalogue licence applies to its current data? Our
proposed use is local retrieval on users' Home Assistant installations, filtering
rural/vegetation fire reports around selected locations and displaying attributed
reports separately from satellite detections. We would not imply endorsement
or replace official warnings.

Please provide any access/registration requirements, polling limits, caching and
retention guidance, and the recommended attribution. A data dictionary covering
incident identifiers, category codes, coordinates, timestamps/timezones, coverage
and the meaning of removal from the feed would also help us avoid incorrect
interpretation. Please forward this enquiry to the appropriate data team if needed.

Thank you,
Janos Bali
TerraLyra

## Deeper licence verification — 2026-09-25

Read the official catalogue API directly:
https://dados.gov.pt/api/1/datasets/prociv-ocorrencias-em-aberto/
It explicitly reports access_type=open, license=cc-by and license_title=CC BY 4.0,
continuous update frequency, and ANEPC as publishing organization. Its two
resources are the legacy GetHistoryOccurrence and GetHistoryOccurrencesByLocation
APIs under prociv.pt/_vti_bin/ARM.ANPC.UI/ANPC_SituacaoOperacional.svc/.
The catalogue's own availability checks report both unavailable in February 2026;
this is historical metadata, not a fresh endpoint availability test.

Followed the official viewer's public ArcGIS metadata rather than assuming that
an unrelated ArcGIS service belongs to ANEPC:
- Enterprise item 29e83f11f7a34339b35364e483e3846f has owner PROCIV,
  access=public and licenseInfo=null.
- Its default visible page embeds ArcGIS Online experience
  ba4aad5cd9014408a7ae30b567fedc75 (owner ANEPCcmota, org j4eW900wJsR0Vv9G).
  That item's licenseInfo is also null.
- The experience configuration references web map
  34ec60d5c79f4e9b8b012efad593e4ce. The anonymous metadata request returns
  an ArcGIS JSON error code 403, so underlying layer licensing could not be
  established. No attempt was made to bypass access control. This does not
  establish that all viewer functions are unavailable or that the map is private.

Metadata routes: /arcgis/sharing/rest/content/items/{id}?f=pjson on the
enterprise host; https://www.arcgis.com/sharing/rest/content/items/{id}?f=json
for Online items. Public configuration is at the corresponding /data route.

Conclusion: the legacy catalogue licence is explicit, not merely implied by
public access. CC BY 4.0 permits sharing and adaptation, including commercial
use, subject to attribution, licence link and change indication, with no implied
endorsement (https://creativecommons.org/licenses/by/4.0/). No separate individual
permission requirement was found for material actually covered by that grant.
An empty current-item licence neither revokes the catalogue grant nor proves
that it covers a different current service. The unresolved question is the
licence/product linkage and supported access, not a proven requirement to ask
permission for all ANEPC data. Limit the draft enquiry to those concrete gaps.

## Further provenance tracing — 2026-09-25

The public resource list of Online experience ba4aad5cd9014408a7ae30b567fedc75
includes config/config.json. Its published configuration references the same
unavailable Online web map, so the earlier /data result is not merely an
unpublished editor configuration mismatch.

An independent official mobile-view chain provides a concrete service identity:
enterprise experience -> dashboard cf8bd8b0179e4f25bcc7eb69e8db31c9 -> public
web map 995fda1ccd2a4a05a8e3cdac47d91e67 -> layer:
https://prociv-agserver.geomai.mai.gov.pt/arcgis/rest/services/Ocorrencias_Base/FeatureServer/0
The map lists itemId 16a8b70d57d7443884a2e34a02e6e954 and refreshInterval=5.
The interval is a viewer setting, not an API rate-limit grant.
Dashboard and map licenseInfo are empty. Service-item metadata returned ArcGIS
403; service and layer metadata requests ended without an HTTP response. These
observations establish neither a reuse licence nor permanent service outage.
No event queries, credential use or access-control bypass were attempted.

Public catalogue discussion 628c97ae07819002712dfa09 contains two user reports
of historical-data download problems in 2022 and no publisher reply in the
returned thread. User comments are not authoritative licence evidence. No
migration statement was found there linking the two old APIs to the current
ArcGIS service.

The draft enquiry can now identify Ocorrencias_Base precisely and ask whether
it is the supported successor covered by the catalogue CC BY 4.0 licence, or
whether ANEPC recommends another endpoint. This narrows the unresolved question;
it is not evidence of a general individual-permission requirement.

## General website terms and government open-data evidence

Further review located a materially relevant official notice:
https://prociv.gov.pt/pt/avisos-legais/politica-de-privacidade/
Under copyright/industrial-property terms (page dated 2023-10-13), the site
allows free personal/public use with source attribution only without profitable
or offensive purposes. Linked sites are subject to their respective copyright
information. This is not equivalent to CC BY 4.0 and must not be assumed to grant
commercial Cloud reuse. Conversely, do not infer that general website wording
revokes an explicit dataset-specific CC BY grant. Applicability to the current
ArcGIS product remains unresolved; open-source distribution alone does not
settle whether an intended use meets a non-profit-purpose condition.

https://mosaico.gov.pt/areas-tecnicas/dados-abertos independently presents the
ANEPC incident dashboard as an open-data reuse example. This supports official
open-data intent but is not a service-specific licence or API contract.

The enquiry should explicitly ask how the dataset's CC BY 4.0 grant relates to
the website's non-profit-purpose wording for the current Ocorrencias_Base data.
Keep local HACS use and any future commercial Cloud use separate in the answer.

## Submission status

2026-09-25: user confirmed sending the ANEPC clarification enquiry. Awaiting
response; no approval or supported endpoint is inferred from submission.
