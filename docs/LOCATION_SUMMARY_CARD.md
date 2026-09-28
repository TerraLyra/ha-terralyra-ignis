# Optional location summary card

Development candidate; not part of an installed release yet. This Hungarian
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

Forecast and restriction panels explicitly report no linked data in this first
version. They do not infer no restriction or low danger. Nearest distance is
omitted until a verified per-location distance association is available.

Validation: model checks cover wrong-location association, partial zero,
initialization/unavailability and invalid counts. Browser checks exercise HA
updates, literal untrusted text, exact details routing and mobile width.
