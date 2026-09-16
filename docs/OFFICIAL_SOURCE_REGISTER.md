# Official-source register — reviewed 2026-09-16

Research status, not a statement of live feed health or authorization to redistribute
all listed products. NSW and Queensland adapters are implemented; other listed sources are research
candidates. This review did not enable feeds or change Home Assistant. Each new
adapter still needs a bounded direct sample/schema/freshness probe.

| Jurisdiction | Official documentation / product | Evidence and remaining gate | Order |
| --- | --- | --- | --- |
| NSW | [RFS feeds](https://www.rfs.nsw.gov.au/news-and-media/stay-up-to-date/feeds) | GeoJSON calendar already shipped. CAP, warnings, ratings/bans are separate extensions. Preserve RFS attribution; check each added product's terms. | 1 |
| Queensland | [QFD dataset](https://www.data.qld.gov.au/dataset/queensland-fire-and-rescue-current-bushfire-incidents) | JSON/XML/CAP-AU/KMZ listed, CC BY 4.0; documented 30-minute incidents cadence. Points describe general areas, not fire spread. Optional report calendar implemented since 0.26.0; see [QFD calendar](QFD_CALENDAR.md). Explicit expiry semantics remain unresolved; catalogue metadata is not live freshness. | 2 |
| Victoria | [CFA feeds](https://www.cfa.vic.gov.au/rss-feeds) | RSS and developer XML/JSON listed; developer access managed by EMV. Resolve applicable redistribution conditions before implementation. | 3 |
| Western Australia | [DFES FAQ](https://www.dfes.wa.gov.au/emergencywa/faq), [Emergency WA terms](https://www.emergency.wa.gov.au/about) | DFES documents SLIP access using ArcGIS/WMS/WFS and RSS/CAP. DFES-066 points and DFES-064 incident areas list CC BY 4.0; DFES-068 warning areas lists CC BY-ND 4.0. SLIP/DFES approval required. See [WA readiness](WESTERN_AUSTRALIA_ADAPTER_READINESS.md); no live sample or guessed map-backend scraping. | 4–5 |
| South Australia | [CFS feeds](https://www.cfs.sa.gov.au/warnings-restrictions/warnings/rss-feeds/) | Separate incidents, warnings, ratings/bans and CAP. Inspect linked resources and reuse terms. Reader refresh advice is not proof of exact publisher cadence. | 4–5 |
| Tasmania | [TFS feeds](https://www.fire.tas.gov.au/Show?pageId=xmlFeedsHome) | CC BY 4.0 with mandatory received-update display and prescribed disclaimer. Select statewide incidents/alerts; preserve required text in implementation after full terms review. | 6–8 |
| ACT | [ESA warnings](https://esa.act.gov.au/be-emergency-ready/warnings-alerts) | Current Incidents HTTPS sample succeeded; explicit CC BY 4.0. Seven ambulance records, no fire sample. Fire types/time semantics remain pending; CAP separate. See [ACT readiness](ACT_ADAPTER_READINESS.md). | 6–8 |
| Northern Territory | [NT fire map](https://pfes.nt.gov.au/fire-and-rescue-service/fire-incident-map) | Documented approximate 10–15-minute updates. Map says points/polygons represent general areas, not fire spread. Machine endpoint and reuse terms remain unverified. | 6–8 |

NSW existing endpoint: https://www.rfs.nsw.gov.au/feeds/majorIncidents.json
ACT documented CAP candidate: https://data.esa.act.gov.au/feeds/esa-cap-incidents.xml
These links are research inputs; they have not all passed direct parser checks here.

## Implementation and next-source decision

NSW and Queensland are implemented. Queensland's opt-in calendar handles incident
points and warning areas separately; it is not an archive or satellite confirmation.
The source register previously described Queensland as a future adapter; that text
was obsolete. See [QFD calendar](QFD_CALENDAR.md) and the historical
[0.26.0 release notes](RELEASE_0_26_0.md).

Next engineering candidate remains Victoria, conditional on developer-feed terms.
The [CFA page](https://www.cfa.vic.gov.au/rss-feeds) distinguishes personal,
non-commercial RSS use from EMV-managed developer XML/JSON access. Do not apply
RSS permission or generic Victorian portal terms to an unverified developer product.
The published developer JSON candidate is
https://data.emergency.vic.gov.au/Show?pageId=getIncidentJSON .
A bounded direct JSON sample succeeded on 2026-09-16: HTTP 200, 2,825 bytes,
four records. See [sample metadata](VICTORIA_SAMPLE_METADATA_2026_09_16.json) and
[adapter readiness](VICTORIA_ADAPTER_READINESS.md). Developer reuse permission
remains unverified; technical reachability alone does not resolve this gate.

On 2026-09-16 the following alternatives still had concrete readiness gaps:

- **South Australia:** the [national official dataset catalogue](https://data.gov.au/data/dataset/south-australian-country-fire-service-current-incidents-rss-feed)
  lists incidents RSS/JSON and warning CAP resources, but marks the licence as
  unspecified. Its general website footer licence is not a resource-specific grant.
  The original South Australian catalogue returned HTTP 403 to the research tool.
  The [CFS feed page](https://www.cfs.sa.gov.au/warnings-restrictions/warnings/rss-feeds/)
  links https://data.eso.sa.gov.au/feeds/prod/cap-au.xml ; the research reader could
  not parse its XML content type. That is not evidence of a feed outage. Confirm
  product terms and inspect bounded payloads before choosing incidents versus CAP.
- **Tasmania:** the [TFS feed page](https://www.fire.tas.gov.au/Show?pageId=xmlFeedsHome)
  gives CC BY 4.0 terms plus mandatory received-update display and a prescribed
  disclaimer. Its statewide incidents link,
  https://www.fire.tas.gov.au/Show?pageId=colBushfireSummariesRss , returned HTTP 410
  to the research tool. Resolve a current official replacement and its own terms;
  do not assume the old licence automatically covers a replacement TasAlert API.

These are dated research observations, not continuous availability checks or a legal
opinion. No new adapter is production-ready on this evidence alone. The next bounded
step is to resolve Victoria's developer conditions, then inspect timestamps, stable
IDs, planned-burn distinctions and geometry using a bounded sample. If access remains
unresolved, evaluate WA's documented SLIP products without guessing map backends.

## Gate record required per product

Record owner, jurisdiction, authoritative landing page, resolved endpoint, checked date,
licence URL/version, required attribution/disclaimer, reuse limits, authentication,
rate limits, format/schema, maximum observed/bounded payload, ID stability, time zone,
geometry role, update cadence, last successful bounded sample, source timestamp,
known exclusions and test fixture provenance. Unknown values remain explicit unknowns.
A publicly viewable map is not sufficient evidence of an integration-ready feed.

## Global coverage worklist and method

Priority means engineering order, not a claimed ranking of annual wildfire severity.
Australia is explicitly first. Next: USA/Canada; Mediterranean; Latin America; then
other recurrently affected regions. Global research must include every country, not
only countries for which an easy API is found.

Initial candidates:
- USA, Canada.
- Portugal, Spain, France, Italy, Greece, Turkey, Cyprus and Balkan countries.
- Chile, Brazil, Argentina, Bolivia, Paraguay; assess Peru, Ecuador, Colombia, Venezuela.
- Algeria, Morocco, Tunisia; South Africa and other affected African countries.
- Indonesia and Southeast Asia; Russia, Mongolia, Kazakhstan, China, India, Nepal.
- Existing user locations (Hungary, Bosnia and Herzegovina, Japan) remain supported
  according to current provider coverage; this list does not declare them equal risks.

Create one country row (and subnational rows where needed) with separate fields for:
1. Recurrent impact: affected years in the latest ten complete years; forest-specific
   burned area and fraction, extreme years, documented population/ecosystem impacts.
2. Data quality: coverage gaps, differences between forest, grassland, savanna,
   agriculture and prescribed burns; missing impact data is not zero impact.
3. Delivery readiness: official incidents/warnings/restrictions/forecast separately;
   access, licence, geometry, freshness and source independence.
4. Decision: candidate, research, access-blocked, ready, implemented, verified; rationale
   and dated evidence. High impact plus poor access stays a priority research item.

Use [GWIS land-cover time series](https://gwis.jrc.ec.europa.eu/apps/country.profile/downloads)
and [EFFIS annual reports](https://forest-fire.emergency.copernicus.eu/reports-and-publications/annual-fire-reports)
for evidence gathering, supplemented with national reports. The all-country quantitative
screen has NOT yet been executed. Refresh it before claiming comprehensive prioritization.
Do not rank countries solely by hotspot counts or total savanna burned area.

USA: NIFC now has an opt-in runtime diagnostic adapter with verified ID-inventory retrieval.
It is disabled by default; map/calendar projection remains separate work.
See [readiness evidence](NIFC_ADAPTER_READINESS.md) and the
[bounded runtime delivery plan](NIFC_RUNTIME_PLAN.md).
Canada candidate: [CWFIS/CWFIF service catalogue](https://cwfis.cfs.nrcan.gc.ca/downloads/docs/en/references/cwfif/cwfis-data-placemat.pdf).
Validate exact current layers and their origin. GWIS/EFFIS satellite-derived context
must not be described as independent field confirmation merely because it is official.

### Access observation in this session

A direct browser-tool open of the Queensland dataset landing page returned a
JavaScript/robot verification page on 2026-09-14. Search-indexed official documentation
was readable, but no current resource payload was validated. This is an access
observation, not evidence that the QFD incident feed itself is down. Resolve the
published resource through an allowed official route before writing its adapter.

### Follow-up: Queensland direct sample succeeded

The official CKAN API was accessible despite the landing-page robot check and
returned the S3 resource URL. On 2026-09-14 at 19:22 UTC a bounded JSON read returned
HTTP 200, 90,629 bytes, 37 records (33 Points, 4 Polygons); Last-Modified was 19:18:27 UTC.
These are sample-specific figures, not expected stable counts. See the adjacent sample
metadata JSON and `OFFICIAL_REPORT_MODEL_PROPOSAL.md` for the mixed schema and time
semantics. Direct access is no longer blocked; the parser and optional calendar were subsequently implemented. The exact upstream
meaning of expiry remains unresolved; see `QFD_CALENDAR.md` for current behavior.
