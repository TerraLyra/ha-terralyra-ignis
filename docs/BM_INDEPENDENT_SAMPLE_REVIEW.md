# BM OKF independent sample review — 2026-09-24

Source: https://www.katasztrofavedelem.hu/10466/RSS_VESZ (BM OKF).
Three notices were evaluated before adapting the reviewed alias vocabulary.
Linked event pages were not fetched. Original RSS and evaluation output remain
local; the repository contains only observations and synthetic regression tests.

## Frozen baseline

| Notice ID | Human interpretation of RSS | Existing matcher |
| --- | --- | --- |
| 92249 | House fire in Gersekarát; several responding-unit towns | No mentions |
| 92248 | Road collision near Somlóvásárhely | No mentions |
| 92247 | Railway collision in Berettyóújfalu; travel/disruption route towns also mentioned | Berettyóújfalu and Biharkeresztes, both from route wording |

Gersekarát and Somlóvásárhely are absent from the inspected bundled cities500
extract. The other gaps include unlisted inflections. The railway result is not
an event-location success simply because its town also appears in a bus route.
This is three observations, not a statistically useful accuracy estimate.
No automatic fire classifier exists in this prototype; the two accident reports
must not be advertised as proof of tested fire/non-fire classification.

## Changes after evaluation

Add manually reviewed forms for Vasvár, Körmend, Zalaegerszeg, Szombathely, Ajka,
Berettyóújfalu and Püspökladány already present in the existing database. Synthetic
regressions preserve route ambiguity and ensure recognized responders do not
supply a missing event location. All 220 offline source tests pass.
These three reports are now development examples, not a future independent test
set. New held-out events are required for further evaluation.

## Remaining gates

- Fill demonstrated settlement coverage gaps using a reviewed, licensed supplement
  or a broader update to the existing GeoNames bundle; do not invent coordinates.
- Add explicit route-context clues and handle complex responder grammar, including
  missing/shared nouns. Retain evidence and unresolved ambiguity.
- Keep mention recognition distinct from event-location verification and incident
  category. No production map wiring is authorized by a text match alone.

The existing database is unchanged. This work adds no requests, HA entities,
calendar changes, history mutations or source-page scraping.
