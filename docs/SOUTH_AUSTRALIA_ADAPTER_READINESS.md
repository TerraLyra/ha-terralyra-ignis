# South Australia CFS access review — 2026-09-18

Status: licence clarification before adapter implementation. No CFS provider added.

## Product-level evidence

The original [SA CKAN package API](https://data.sa.gov.au/data/api/3/action/package_show?id=south-australian-country-fire-service-current-incidents-rss-feed)
was accessible on 2026-09-18 despite earlier browser access failures. It identifies
CFS Current Incidents RSS Feed and reports `license_id: cc-by-nc-nd`, title Creative
Commons Attribution-NonCommercial-NoDerivs, and a CC BY-NC-ND 4.0 licence URL.
Its metadata modification date is 2022-05-05, so confirm whether these terms remain
the intended current conditions. The resource records provide no overriding
`license_id`; absence of a per-resource value is not an additional licence grant.

The package lists:
- RSS: https://data.eso.sa.gov.au/prod/cfs/criimson/cfs_current_incidents.xml
- JSON: https://data.eso.sa.gov.au/prod/cfs/criimson/cfs_current_incidents.json
- CAP: https://data.eso.sa.gov.au/prod/cfs/criimson/cfs_cap_incidents.xml

This is metadata evidence, not a live payload/availability or completeness test.
The current CFS feed page links a different CAP path,
https://data.eso.sa.gov.au/feeds/prod/cap-au.xml . Do not assume endpoint equivalence
or transfer terms between paths without confirmation.

The [national harvested catalogue](https://data.gov.au/data/dataset/south-australian-country-fire-service-current-incidents-rss-feed)
shows Licence Not Specified. The primary package's positive licence evidence
supersedes our earlier conclusion that only unspecified metadata was available.
The [CFS website copyright](https://cfs.sa.gov.au/home/copyright/) grants CC BY 4.0
for site content with exceptions and precedence for specific terms; it does not
establish that the differently licensed external feed is unrestricted.

## Development decision

[CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/) restricts
commercial use and distribution of adapted material. Mere format conversion does
not itself create an adaptation; this review does not claim every filter or parser
requires a new licence. Clarify the intended local HACS display/filtering/caching
with CFS and request a separate grant for any commercial service or other use beyond
the licence. Open-source code does not automatically make every downstream use
non-commercial.

Notify the user before substantial adapter work; this was done on 2026-09-18. No
credentials, registration or approval were obtained. No provider-specific runtime,
raw feed fixture, event transformation or polling was added. The existing HA and
history are unaffected. A clarification request is prepared in
[provider request drafts](PROVIDER_ACCESS_REQUEST_DRAFTS.md).

## Contact and questions

Use the official national dataset page's **Ask a question about this dataset** form,
which states it sends the question to the publisher. The older catalogue also names
an individual contact, but the form is preferable to assuming that person's current
role. No form was submitted by the assistant.

Ask whether CC BY-NC-ND 4.0 is current for each RSS/JSON/CAP product; whether local
attributed HACS filtering/display/caching is covered; applicable request limits,
retention and disclaimers; permitted commercial use; and which CAP endpoint is the
supported product. After terms are settled, obtain schema, IDs, source-time semantics,
planned-burn distinctions and completeness/geometry evidence before implementation.
