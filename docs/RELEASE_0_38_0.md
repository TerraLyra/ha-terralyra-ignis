# 0.38.0 — Easier dashboard setup

Prepared for stable publication; not published yet.

## Changes

- Select a location forecast in the summary editor without copying coordinates
  into YAML. When its radius or coordinates change, review and apply the new
  values using the explicit refresh button.
- Summary labels, source guidance, forecast validity and setup review follow HA's
  UI language: Hungarian for Hungarian, English otherwise. Custom titles, place
  names and attribution stay unchanged.
- The map editor lists only matching IGNIS report-source switches. A saved binding
  with conflicting source metadata is explained and its layer stays hidden.
  Legacy bindings without metadata remain compatible.
- Select monitoring and alert circles with a checkbox. Equal radii use one circle;
  these are configured boundaries, not fire perimeters. Existing source options
  and explicit clustering are preserved. Native show_all mode is explained.

## Upgrade

1. Once published, update through HACS and restart HA at a convenient time.
2. Fully reload the browser or Companion App frontend.
3. Keep existing card resources and bindings. If old code persists, update the
   existing resource query to `?v=0.38.0`; do not add duplicate resources.
4. In the optional card editors, review the location, forecast and map bindings.
   No provider or notification automation is enabled by selecting a binding.

There is no data migration. Existing location radii, history, satellite matching
and notification rules are unchanged. No language model or new provider is added.

## Validation and limits

The feature PRs passed all GitHub checks. Local validation passed 38 frontend
checks and isolated browser tests covering explicit selections, changed forecast
bindings, language switching, source mismatch handling and circle configuration.
Release-preparation CI must also pass before publication. A clean-install trial,
full production upgrade acceptance and notification delivery remain unverified.

See [first setup](FIRST_STEPS.md), [card resources](CARD_RESOURCES.md) and
[onboarding acceptance](ONBOARDING_ACCEPTANCE.md).
