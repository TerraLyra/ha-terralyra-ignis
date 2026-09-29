# Optional location summary card

Merged in PR #75 and separately installed on the user's HA dashboard. Not yet
bundled into a new HACS release. This Hungarian
card reads existing per-location operational-status entities only. It never
calls a service, fetches a provider, or changes HA state/history.

When installing a reviewed version, copy frontend/ignis-location-summary.js to
/config/www/ignis-location-summary.js, register it as a JavaScript module resource
at /local/ignis-location-summary.js, then add a manual dashboard card:

```yaml
type: custom:ignis-location-summary
entity: sensor.REPLACE_WITH_LOCATION_STATUS_ENTITY
location_id: REPLACE_WITH_EXACT_LOCATION_ID
```

Choose the IGNIS location operational-status sensor in Developer Tools → States.
Copy its exact entity ID and location_id attribute; do not guess from translated
names or entity suffixes. A mismatch fails closed. Use one card per place.
A custom title is optional. The details button opens that exact entity.

The counts represent active tracked satellite incidents within this location's
radius, plus multi-source corroboration. They are not raw pixels or official
incident reports. During partial or delayed retrieval, counts keep their existing
snapshot semantics and the limitation stays visible. Unavailable/unknown entity
states and initialization suppress numbers, including old cached counts.
No backend entity semantics or Recorder data are changed.

Source health is shown separately. The latest successful receipt may belong to
only one source; it is not evidence that all sources are fresh, nor an ignition
or acquisition time. Missing timestamps remain missing.

The restriction panel explicitly reports no linked data. It does not infer no
restriction or low danger. The optional nearest-distance line uses nearest_incident_distance_km on the
same explicitly associated location-status entity. Older integration versions
without this attribute show no verifiable distance. The backend selects the
minimum current distance among NEW/CONTINUING incidents whose exact location
match is inside that location's radius; it never uses global Home distance or
historical minimum distance. Partial retrieval retains snapshot semantics and
the source-status warning. No candidate means missing distance, not zero.
This backend addition requires an integration update and HA restart as well as
the separate frontend update; it is not installed by changing the card alone.

Validation: model checks cover wrong-location association, partial zero,
initialization/unavailability and invalid counts. Browser checks exercise HA
updates, literal untrusted text, exact details routing and mobile width.


## Optional near-home forecast binding

The new main-branch candidate accepts an explicit binding after the installer
verifies that the monitored location is the HA home point. The existing FRMv3
coordinator fetches only for HA home, not for every monitored location.

```yaml
forecast:
  entity: sensor.REPLACE_WITH_FIRE_RISK_TODAY
  location_id: REPLACE_WITH_SAME_EXACT_LOCATION_ID
  latitude: 47.0  # example only: verified HA home latitude
  longitude: 19.0 # example only: verified HA home longitude
```

Do not use these example coordinates in production. Compare the monitored
location configuration with HA home; copy the actual forecast sensor ID and
verify its near_home scope and sample coordinates. A different location ID,
scope or sample point fails closed. This explicit configuration is an installer
assertion, not automatic discovery of an entity-to-location relationship.

The card selects the unique entry for the current UTC product date, not the
sensor's first-day state. Expired, ambiguous, unknown and unavailable data do not
produce a current risk value. The receipt time is generated_at in this provider's
implementation, not model issuance; receipts older than the normal 12-hour refresh
interval are labelled delayed. This does not prove model freshness. Times are
formatted in the HA timezone; product dates remain explicitly UTC.

A browser/HA state refresh updates the view; the card makes no provider requests.
The binding is optional and existing unbound cards continue to work. Replace the
existing JS resource and change its version query after review, without adding a
duplicate resource. No backend or Recorder migration is required.
