# Provider access requests — drafts, not sent

Prepared 2026-09-18. Use the organization's working mailbox. Add the sender's actual
name/role; no legal entity status, existing approval or affiliation is implied.

## Tasmania

Permission route rechecked 2026-09-21 against the official
[developer-feed FAQ](https://alert.tas.gov.au/about-app). Draft remains unsent.

To: info@alert.tas.gov.au
Subject: TerraLyra IGNIS – request for TasALERT developer data-feed access

Hello TasALERT team,

We are developing TerraLyra IGNIS, an open-source Home Assistant integration.
Your About App page directs developers to request permission to access TasALERT feeds.

We would like to display attributed official bushfire incident reports, warnings
and planned-burn information around user-selected locations. These would remain
separate from satellite observations and would not replace official emergency advice.

Could you provide the approved endpoints, access process and applicable developer
terms for a publicly distributed integration running locally on each user's Home
Assistant installation? Please clarify whether each user needs their own account,
permitted filtering/display/caching, required attribution/disclaimers, request limits
and retention conditions. We would not distribute a shared credential in public code.
Any future commercial cloud use would be assessed separately.

Please also share the schema, event identifier lifecycle, timestamps/timezones,
test/cancellation markers and completeness/pagination rules. We have not implemented
or enabled a production TasALERT adapter.

Thank you.

## Western Australia

To: statepublicinfo@dfes.wa.gov.au
Subject: TerraLyra IGNIS – DFES-066 access and distributed local integration enquiry

Hello DFES State Public Information team,

We are developing TerraLyra IGNIS, an open-source Home Assistant integration, and
would like to request access to DFES EmergencyWA Incident Points (DFES-066).

Our intended initial use is local retrieval and attributed display of relevant
incident points around user-selected locations. We would distinguish official
reports from satellite observations and would not infer fire spread from a point.

The catalogue lists SLIP registration and dataset approval, CC BY 4.0 alongside
EmergencyWA conditions, and Government Use Only labels on service resources.
Could you confirm eligibility and the correct access process for this public,
distributed local integration? Should each Home Assistant user register separately?
We would not publish shared credentials or assume permission for a cloud relay.

Please confirm permitted filtering, display, caching/retention, attribution and
request limits, and provide the current service/schema documentation, coordinate
reference system, identifier lifecycle, timestamp semantics and pagination rules.
Incident areas and warning areas would be considered separately; this request does
not assume that DFES-066 terms apply to DFES-064 or DFES-068. Any future commercial
cloud service would also be assessed separately.

Thank you.

## South Australia CFS — licence clarification

Route: the official dataset page's "Ask a question about this dataset" form:
https://data.gov.au/data/dataset/south-australian-country-fire-service-current-incidents-rss-feed
Subject: TerraLyra IGNIS – CFS incident feed licence and developer-use clarification

Hello CFS data team,

We are developing TerraLyra IGNIS, an open-source Home Assistant integration, and
are checking the applicable terms before implementing a South Australian provider.

The original data.sa.gov.au catalogue API lists CC BY-NC-ND 4.0 for the CFS Current
Incidents RSS Feed package, including the JSON resource at:
https://data.eso.sa.gov.au/prod/cfs/criimson/cfs_current_incidents.json
The national catalogue mirror instead shows Licence Not Specified, while the CFS
website has a general CC BY 4.0 statement. Could you confirm the current terms for
this specific JSON product and any separate conditions for RSS or CAP?

Our proposed initial use is local fetching, filtering around user-selected locations,
and attributed display of official reports on each user's Home Assistant installation,
with temporary caching and clear links to official information. We would not imply
endorsement or turn incident points into fire-extent or safety claims.

Please clarify whether this use is covered, the required credits/disclaimers,
request intervals and retention rules. If any part needs additional permission,
please advise the process. Any future commercial Cloud use would need to be
considered separately; no commercial-use permission is assumed.

Your current feed page links /feeds/prod/cap-au.xml while the catalogue lists
/prod/cfs/criimson/cfs_cap_incidents.xml. Please identify the supported CAP product
and its terms if it is suitable for a future, separately scoped warning adapter.

Thank you.

## Northern Territory — supported feed and reuse clarification

Routing: Corporate Communications and Recognition Unit identified by the
[PFES copyright page](https://pfes.nt.gov.au/node/849); a dedicated developer
email has not been verified. Draft only, not sent.

Subject: TerraLyra IGNIS – NT Fire Incident Map developer feed and reuse enquiry

Hello NT Fire Incident Map team,

We are developing TerraLyra IGNIS, an open-source Home Assistant integration.
Could you identify the supported machine-readable product behind the official
NT Fire Incident Map and the current developer access and reuse conditions?

Our proposed use is local fetching on each user's Home Assistant installation,
filtering around selected locations and attributed display of official reports.
We would distinguish incidents, warning areas and planned burns, preserve source
status and update times, and not imply endorsement or replace official warnings.

Does this publicly distributed HACS integration require written approval,
registration or individual credentials? Please confirm required attribution,
request intervals, temporary caching and retention. Any future commercial Cloud
use would be considered separately.

We would appreciate documentation on identifiers and reuse, timestamp meanings
and offsets, category/status codes, geometry, completeness and what removal from
the feed means. We would not infer an all-clear from closure or disappearance.
If another team manages this product, please direct us to that team.

Thank you.
