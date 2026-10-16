# 0.40.4 — Clearer dashboard setup and empty observations

The location summary now explains when no satellite observations are tracked in
its monitored area and time window. This wording requires available source status,
a zero incident count and no nearest distance. Partial, delayed, unavailable and
contradictory data retain the missing-distance message. An empty result is not an
all-clear.

The map editor distinguishes an optional report switch that can be selected from
one that is absent, and directs users to the appropriate setup step. It also
reviews monitoring-circle data: disabled display, loading, missing areas, valid
geometry and incomplete/unavailable records. Inner alert circles are not extra
locations. Available geometry does not guarantee visibility under all map filters
or clustering settings.

These improvements are available in Hungarian and English. They do not enable
providers, change radii or replace saved dashboard configuration. No storage
migration, history deletion or source request is required.

Update through HACS, restart Home Assistant, then fully reload the browser or
Companion App frontend. For stale manually registered card resources, follow
[card resource recovery](CARD_RESOURCES.md#later-updates-and-rollback).

Implementation PRs #193–#195 each passed all 27 automated checks. Targeted tests
cover empty/recovery states, optional source bindings and invalid area geometry.
The release candidate has not been installed on the production Home Assistant.
