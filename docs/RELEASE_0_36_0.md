# 0.36.0 — Easier dashboard setup

Release candidate; publication is pending.

## Changes

The optional IGNIS report map now has a Hungarian/English visual editor for its
title and explicit Canada/NIFC map visibility switch bindings. Existing map
entities, zoom and advanced configuration are retained. No switch is chosen
automatically. Select the correct IGNIS map switch; the list does not infer
provider identity from translated entity names.

The editor explains unbound, invalid, loading, missing, unavailable, off and on
bindings. It never toggles a switch or enables a provider. An enabled map switch
does not prove that fresh reports exist. Live state updates retain a title being
edited. Location circles and other advanced map options still use the code editor.

The Hungarian location summary adds concise guidance for authentication errors,
failed retrieval, delayed data, missing products and initialization. Successful
retrieval is kept distinct from observation freshness.

First-setup instructions now consistently describe the bundled card resources.
Offline BM review recognizes the observed Sárisáp, Bajna and Nyergesújfalu forms
and singular responder-unit wording. This does not enable automatic BM geolocation.

## Upgrade

1. Update through HACS and restart Home Assistant at a suitable time.
2. Fully reload the browser or Companion App frontend.
3. If bundled resource URLs introduced in 0.35.0 are already configured, retain
   them. Older `/local/` resources need the [one-time migration](CARD_RESOURCES.md).

Existing dashboard configuration, source opt-ins, radii, notification automations,
blueprints and history are preserved. No new source is enabled by this release.

## Validation boundary

Automated frontend and browser tests cover preserved configuration, missing
bindings, both editor languages, mobile layout and title retention during state
updates. Offline BM tests cover the reviewed aliases and responder context.
Fresh-install and unaided-user acceptance remain outstanding; see
[onboarding acceptance](ONBOARDING_ACCEPTANCE.md).
