# Optional location summary card

> **IGNIS 0.35.0+:** cards are bundled with the integration. See
> [one-time resource setup, updates and older-version migration](CARD_RESOURCES.md).

This optional card reads per-location operational-status entities and
explicitly bound forecast sensors. It never
calls a service, fetches a provider, or changes HA state/history.

On IGNIS 0.35.0+, register `/terralyra_ignis/cards/ignis-location-summary.js`
as a JavaScript module resource once. HACS delivers the matching file; no manual
copy is needed. In dashboard edit mode, add
**IGNIS helyszínösszefoglaló**, then select the monitored location's status sensor
from the visual editor. It copies the exact location ID from that sensor; no
entity-name guessing or location-ID copying is needed. You can also enter a custom
title. No location is selected automatically, even if only one is available.

The editor lists sensors with the location operational-status attributes. If
none are available, it explains how to enable a monitored location and wait for
its sensor. A temporarily missing configured sensor is retained rather than
silently replaced. In 0.38.0+, the editor and card follow
the Home Assistant UI language: Hungarian for Hungarian, English for other
languages. Before HA connects, the historical Hungarian default is preserved.
Custom titles, location names and source attribution are displayed unchanged.

In 0.38.0+, choose a matching sensor
under **Előrejelzés (nem kötelező)** in the visual editor. This copies its location,
coordinates and forecast radius without enabling a provider. The code-editor
examples below remain supported. Existing forecast and advanced configuration
fields are preserved when editing the title or location. After changing location, review the forecast binding too: a mismatched
binding stays hidden with an explanation, never showing another place's risk.

## Next release: simpler setup navigation

Merged after 0.38.1, not yet included in a stable release:

- Unique location names appear without technical IDs; duplicate names retain IDs
  to make the selection unambiguous. The selected entity remains explicit.
- Editor links open IGNIS location/radius settings and the English or Hungarian
  first-setup guide in a separate tab, preserving the unfinished card editor.
  Opening a link does not change configuration or enable sources.

## Advanced manual configuration

The visual editor above is the recommended setup path. Existing manual YAML remains supported:

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

The legacy near-home binding remains supported after verifying that the
monitored location is the HA home point. The legacy FRMv3 coordinator fetches
for HA home; separately enabled location forecasts use the binding below.

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

## Per-location forecast binding (0.32.0+)

In integration options, open monitored-location management, select **Location
fire-risk forecast**, choose an enabled covered location and enter its independent
forecast radius. A new location forecast sensor is created after options reload;
the initial request is deliberately delayed by roughly 30 seconds to five minutes.
The existing Home forecast sensors are preserved.

Use the new sensor's actual entity ID and copy its requested `location_id`,
`latitude`, `longitude` and `forecast_radius_km` attributes into the binding:

```yaml
forecast:
  entity: sensor.your_location_fire_risk_forecast
  location_id: your-stable-location-id
  latitude: 47.5
  longitude: 19.0
  radius_km: 50
```

The location ID must also match the card's top-level `location_id`. These are
requested coordinates, not `sample_latitude`/`sample_longitude`, which can point
to a nearby valid forecast pixel. The radius is the forecast radius, not the
satellite-monitoring radius. After moving/resizing a location, update the binding;
a mismatch deliberately hides the risk. In the updated visual editor,
**Előrejelzés hozzárendelésének frissítése** shows the new coordinates and forecast
radius and copies them only when clicked. A missing or different-location sensor
is never substituted automatically. Nothing here enables additional providers
or automatically edits a dashboard.
