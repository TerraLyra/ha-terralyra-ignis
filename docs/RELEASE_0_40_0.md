# 0.40.0 — Optional TasALERT reports

## Changes

- Add TasALERT official incident reports around enabled monitored locations.
- Keep bushfires, planned fuel-reduction burns and structure fires distinct, with
  original status, record creation/update times, source links and CC BY 4.0 attribution.
- Share paced retrieval and persistent backoff across IGNIS entries.
- Add explicit first-use initialization, diagnostic status and conservative storage recovery.
- Hide TasALERT map controls until the corresponding map switch is enabled and bound.

TasALERT is off by default. These are official reports, not satellite detections;
source status does not prove current fire activity. No linked incident pages are
fetched. No calendar events or satellite notifications are created by TasALERT.

## Upgrade and optional setup

1. Update through HACS, restart Home Assistant and fully reload the browser or
   Companion App frontend. Keep the existing dashboard resource registrations.
   If old JavaScript remains cached, change the existing map resource query to
   `?v=0.40.0` rather than adding a duplicate resource.
2. To use TasALERT, first configure an enabled monitored location in Tasmania.
3. In Developer Tools → Actions, run `terralyra_ignis.initialize_tasalert` with the
   loaded IGNIS config entry and `confirm_first_use: true`. This is only for first
   use, not a reset after deleting established storage.
4. Turn on that entry's TasALERT map switch. In the IGNIS report map editor,
   select it as the TasALERT map-switch binding.
5. The diagnostic sensor is optional and disabled by default. Enabling it also
   opts into retrieval, independently of the map switch. Disable both consumers
   to stop their retrieval requests; other entries may still use the shared feed.

Empty responses and retrieval failures retain earlier data without claiming it
is fresh. Corrupt storage blocks requests. The administrator recovery action
`terralyra_ignis.recover_tasalert` requires `confirm_review: true`; it only reads
valid existing storage and preserves waits. See [technical behavior](TASALERT_FEED_REVIEW.md).

## Validation

The feature passed 1,253 HA tests and 130 subtests in CI, with 100% config-flow
coverage, plus offline source tests and browser checks. Isolated HA checks covered
marker creation/removal, persisted reload, initialization, recovery and failures.
Production upgrade acceptance remains to be performed after installation.
