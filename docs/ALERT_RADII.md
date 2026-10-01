# Monitoring and satellite alert radii

Each enabled monitored location has two concentric radii:

- **Monitoring radius:** observation selection, incident tracking and map coverage.
- **Alert radius:** satellite incident entry notifications. It must be positive and
  no larger than the monitoring radius; equality is allowed.

Edit both under the integration's monitored-location options. Reducing monitoring
below an explicit alert radius is rejected; adjust both together. Existing stored
locations without an alert radius retain their monitoring radius as the fallback.
No history migration or deletion is required. The fire-risk forecast radius remains
independent. Official reports do not generate this satellite alert event.

## Event semantics

`terralyra_ignis_fire_alert` is emitted for a newly observed incident inside an alert
radius, or a newer observation entering it. Every enabled location is evaluated
independently. One event contains the qualifying `alert_locations` list, including
location identity, name, distance and alert radius. Distances are evaluated before
rounding; the boundary is included. The payload also contains `config_entry_id`,
incident attributes and `alert_reason: entered_alert_radius`.

The first processed snapshot after startup or a location configuration change
establishes a quiet baseline. An incident remaining inside does not alert again;
a newer outside observation followed by a newer inside observation does. Added
corroborating satellite tracks do not repeat an alert for an already-inside incident.
A bounded, 10,000 track/location in-memory cache preserves transitions across
missing or inactive snapshots. Evicted identities may subsequently be treated as
new. This cache does not change stored incident history.

`terralyra_ignis_new_fire` and existing trend events remain observation events and
are not restricted to the alert radius. Existing user automations therefore keep
their previous behavior until explicitly migrated.

## Notification automation

### Ready-to-use phone blueprint

The [satellite notification blueprint](../blueprints/automation/terralyra_ignis/satellite_alert.yaml)
lets you select an IGNIS installation, a Companion App phone and Hungarian,
English, German, Spanish, French or Italian message text. Requires IGNIS 0.33.0+
and Home Assistant 2026.9+.

1. Under **Settings → Automations & scenes → Blueprints → Import blueprint**,
   paste the GitHub URL of the blueprint YAML file from the version you use.
2. Create an automation from it, select the IGNIS installation and phone, then
   choose the notification language and save.
3. If replacing an existing notification automation, disable that automation
   yourself to avoid duplicate messages. Keep its previous thresholds in the
   locations' alert-radius settings.

The blueprint is imported separately; a HACS integration update does not install
or update it. Your existing automations are not changed. Phone notification
permissions must be enabled in the Companion App and phone settings.

Example Hungarian notification:

> **Tűz észlelés Home közelében**
>
> Tűz észlelve 42,5km-re a Home ponttól északkeletre

English: **Fire detected near Home** / **Fire detected 42.5 km northeast of Home**.
Each affected location uses its own distance and direction. Multiple affected
locations share one notification, which can be longer. Unknown directions are
omitted. The blueprint supports all six current IGNIS languages for notification
text; it does not automatically follow the Home Assistant interface language.
The blueprint setup labels remain English/Hungarian. English uses a decimal
point; the other five message languages use a decimal comma. Location names
remain exactly as entered by the user.

Manual **Run actions** without an event does not send anything. Template tests
use fictional events offline and do not send push notifications. After startup,
wait for a genuinely new qualifying satellite observation: existing incidents
form the quiet baseline described above. This is a satellite observation notice,
not an official emergency warning.

### Custom automation

Use the new event rather than a generic geolocation state-change trigger. Replace
the notification action with your device's action. If several IGNIS installations
are configured, add a `config_entry_id` event-data filter.

```yaml
alias: IGNIS satellite alert
triggers:
  - trigger: event
    event_type: terralyra_ignis_fire_alert
actions:
  - action: notify.YOUR_DEVICE
    data:
      title: Satellite fire observation
      message: >-
        {% for place in trigger.event.data.alert_locations %}
        {{ place.location_name }}: {{ place.distance_km }} km
        (alert radius {{ place.alert_radius_km }} km).
        {% endfor %}
mode: queued
```

Before migrating an existing notification automation, preserve its actual previous
threshold in each location's alert setting. Do not automatically widen it to the
monitoring radius. Disable the replaced notification trigger to avoid duplicates.
The integration does not rewrite user automations.

## Map and summary

The monitoring-area geolocation source supplies an outer monitoring circle and,
when smaller, an inner alert circle. Equal radii produce one circle. Both radius
values are exposed as attributes; the optional location-summary card displays them.
Add `terralyra_ignis_monitoring_areas` to a native map's geolocation sources to show
the circles. Their appearance follows the Home Assistant map renderer.
