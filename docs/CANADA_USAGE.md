# Canada CWFIF official reports

IGNIS can display official Canadian source reports alongside, but separately from,
satellite detections. Source: Canadian Forest Service / CWFIS / Natural Resources
Canada, [Active Wildfires in Canada](https://cwfis.cfs.nrcan.gc.ca/en/catalogue/results/bd641635-d30d-4b77-abc0-d6b59b1e8a00).
The product is offered under the [Open Government Licence – Canada](https://open.canada.ca/en/open-government-licence-canada).
No separate application is indicated for this attributed use in the verified product
catalogue. This does not establish request quotas or permission for other products.

## Enable

1. Install a release containing this feature and restart Home Assistant. Existing
   satellite and NIFC configuration does not need to be reset.
2. Keep at least one relevant monitored location enabled. In the IGNIS entity list,
   enable **Canada CWFIF source status**, which is disabled by default.
3. For genuine first use, an administrator runs
   `terralyra_ignis.initialize_canada` in **Developer tools → Actions**, selects a
   loaded IGNIS entry and confirms first use. All IGNIS entries share this state.
   Never use initialization after deleting storage or to reset a request pause.
4. Optional: turn on the **Canada CWFIF official reports map** switch and enable
   the **Canada CWFIF official reports** calendar. Names vary with the HA language.
   These use the same shared client, so enabling more views does not multiply requests.

The first successful response makes source status available. Initialization alone
with no enabled consumer does not fetch. Nationwide requests send no monitored-point
coordinates upstream; filtering and distances are calculated locally. Successful
requests are separated by one hour. Failure retries start at five minutes and back
off; longer server pauses are respected. These intervals are local design choices,
not a quota guaranteed by the provider. Manual refresh cannot bypass them.

## Interpret

- **Not requested:** first request or preparation is pending. Check
  `activation_status` and `initialization_status` for initialization requirements.
- **Available:** a validated response was retrieved; it does not prove fresh fire activity.
- **Waiting:** no validated response is cached and another attempt is pending.
- **Retained response:** a previous successful response remains after refresh failure.
- **Review required:** investigate source access or storage before recovery.

The status sensor counts nationwide source records, not fires near a selected point.
Map markers and calendar entries are filtered to enabled monitored circles. Distances
use the nearest matching monitored point, with all matches identified. A map display
limit of 500 matching reports is explicit; IGNIS does not silently select a subset.

Calendar entries use the source's `status_date`, with its explicit timezone offset.
The one-second event is a UI marker for a reported status update, not ignition or fire
duration. Record validity and initial/situation-report dates have separate meanings.
Older reports remain possible. A missing region, zero records or a removed record
never establishes an all-clear. Unknown control/category values and containment -1
remain unknown. Official reports do not become satellite incident history or alerts.

## Recovery and data preservation

Resolve the source/storage problem, then an administrator may run
`terralyra_ignis.recover_canada` with explicit review confirmation. Recovery preserves
cached reports and known longer waits, and imposes at least one hour before a request.
Pending disk work, missing/corrupt state or a missing cooldown cannot be reset this way.
Do not delete `.storage` files; restore a validated backup when needed.

Canada uses its own `terralyra_ignis.canada_state` store. Existing incident history and
other providers are not migrated. Disable the map, calendar and status sensor to stop
Canada polling. Removing a map marker does not delete stored satellite history.
