# 0.32.1 — Official report display fixes

## Integration change

Canada map reports now expose the last successful retrieval timestamp already
stored by the source coordinator. Failed refreshes retain the previous successful
time; missing values remain unknown. Source report dates and entity identities
are unchanged. Receipt time does not establish current fire activity or completeness.

The defusedxml requirement is now >=0.7.1 rather than an exact 0.7.1 pin, retaining
the minimum supported version. Other integration dependency pins are unchanged.

## Optional map card

The separately installed report map labels source descriptions and distinguishes
feeds without narrative fields, missing source descriptions, unrequested stored
fields and unknown availability. Long display text carries a truncation notice.

Canada and NIFC retrieval states have English/Hungarian labels with the original
code retained. Known retrieval failures/cooldowns explicitly identify a retained
earlier report. Incident status and source times are preserved; successful
retrieval is not described as fresh fire activity.

## Installation

For the Canada receipt attribute, update the integration through HACS and restart
Home Assistant at a suitable time. No automatic restart, history reset or
configuration migration is required.

For the optional map dialog changes, replace the existing installed map-card file
with the matching `ignis-report-map.js` release asset. Keep its configured filename
or update the existing resource URL to the new file, using a fresh version query
such as `?v=0.32.1`, then reload the browser. Do not add a duplicate resource.
The card alone does not require a HA restart. Previously installed main-branch
card changes from #103/#104 already provide the same dialog behavior.

## Scope and validation

No new provider is enabled. INPE, GWIS, Himawari and Castilla y León research work
is not wired into production entities, calendars or scheduled polling.
Optimization and historical-counter investigation remain paused.

Regression coverage checks retained receipt time after a failed Canada refresh,
unknown receipt values, unchanged source dates and entity identity. Frontend tests
cover safe source text, missing-description feedback and provider-specific
retrieval labels. All exact release-candidate CI checks must pass before publication.
Post-installation acceptance of the Canada attribute remains a separate live check.
