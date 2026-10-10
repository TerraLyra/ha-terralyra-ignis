# Active-fire monitoring-radius map overlay

TerraLyra IGNIS exposes an outer monitoring circle for every enabled monitored
location. Since 0.33.0, a smaller alert radius also creates an inner alert circle;
equal radii use one circle. These native Home Assistant geolocation entities use the separate
`terralyra_ignis_monitoring_areas` source so the overlay is optional and existing
fire-map cards are not changed by an integration update.

## Recommended map card

```yaml
type: map
geo_location_sources:
  - source: terralyra_ignis
    label_mode: icon
  - source: terralyra_ignis_monitoring_areas
    label_mode: icon
    focus: false
cluster: false
hours_to_show: 24
```

`focus: false` prevents distant monitoring centers from forcing a global map
view. `cluster: false` prevents a center marker from being grouped with nearby
fire markers, keeping its radius decoration consistently visible.

The radius is stored in metres in the generic `gps_accuracy` compatibility
attribute because that is the circle decoration supported by the native Home
Assistant map. It is also exposed as `monitoring_radius_km`, together with
`map_circle_meaning: active_fire_monitoring_area`, to make its meaning explicit.

## Limits

- The outer circle is the user-configured active-fire monitoring boundary; the
  inner circle, when present, is the satellite alert boundary.
- It is not a measured fire perimeter, satellite footprint, uncertainty radius,
  evacuation area, or safety zone.
- It provides no guarantee that every fire inside it will be detected.
- The map does not automatically fit the full circle; zoom can be adjusted in
  the card or interactively.
- Changing a location, its enabled state, or its radius reloads the integration
  and recreates the corresponding overlay from the saved settings.

## Optional IGNIS map visual editor

Since stable 0.38.0, the IGNIS report-map editor
includes **Monitoring and alert circles** / **Megfigyelési és riasztási körök**.
Selecting it adds the monitoring-area source with icon labels and `focus: false`.
If clustering has not been configured, it sets `cluster: false` so the circle
centres remain separate. Existing source options and explicit clustering settings
are preserved; the editor explains when clustering can hide circles.

Clearing the checkbox removes only this source from the card. It does not disable
monitored locations or change their radii. With native `show_all: true`, separate
circle filtering is disabled; the editor explains that this advanced setting must
first be changed in the code editor. Equal radii still use one circle.
