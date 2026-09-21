# IGNIS public development roadmap

Status reviewed on 2026-09-21 against stable 0.27.0.

## Delivered

- Optional NIFC / WFIGS source status, timed calendar and location-aware report map
  shipped in 0.27.0. Administrator first-use initialization, bounded shared retrieval,
  persisted cooldowns and recovery diagnostics are included. See [NIFC usage](NIFC_USAGE.md).
- Initial live smoke checks confirmed a later successful retrieval and one matching
  map/calendar report with consistent location-relative distance and source time.
  This is sampled validation, not continuous uptime or exhaustive coverage evidence.
- Standalone basic observation-model packaging pilot builds a wheel from an
  allowlisted source archive. Shared consumer checks cover bundled and installed
  models on supported CI environments. See [package scope](BASIC_MODEL_PACKAGE.md).
- HA compatibility imports, existing IDs/history handling and per-location source
  health remain covered. No Cloud account or private runtime package is required.
- Current repository links and pinned CI tools are in place.

## Open work and limitations

- [Historical counter discontinuity](https://github.com/TerraLyra/ha-terralyra-ignis/issues/41):
  the original historical cause remains unproven. Investigate available evidence;
  do not delete or rewrite user history, or assume access to an old machine/backup.
- Live smoke checks do not prove full history equivalence, restart/outage recovery
  or uninterrupted operation. Those scenarios have automated coverage but are not
  claimed as completed live acceptance tests.
- Source receipt freshness is not incident freshness, national completeness or an
  emergency all-clear. Map/calendar limits remain documented per provider.
- The standalone package is an unpublished experimental model subset, not a complete
  independently deployable Core or stable SDK. The integration parent still uses HA.
- PyTurboJPEG 1.8.3 remains a required test dependency through HA camera imports,
  matching the tested HA 2026.9.3 camera manifest. Reassess together with HA;
  no separate JPEG runtime requirement is added to IGNIS.

## Australian provider queue

| Source | Current position | Next gate |
| --- | --- | --- |
| NSW RFS / Queensland QFD | Existing optional report calendars | Maintain compatibility and source-specific semantics |
| Victoria | Offline inspectors complete; user submitted access request on 2026-09-20 | Await developer terms and resolve remaining time/schema evidence before runtime work |
| ACT | Offline experimental research only | Real timestamp semantics and DST evidence; no production entities/calendar |
| Tasmania TasALERT | User confirmed access request sent on 2026-09-21 | Await response, then review granted endpoints and terms |
| Western Australia DFES | Access-request draft ready | Clarify dataset approval and distributed local authentication |
| South Australia CFS | Licence-clarification draft ready | Resolve product-specific reuse terms |
| Northern Territory | Access preflight and enquiry draft ready | Confirm supported feed and reuse scope |

Victoria and Tasmania submissions are confirmed by the user; other drafts remain
unsent unless separately confirmed. No approval is inferred from a publicly reachable endpoint.
See [access preflight](PROVIDER_ACCESS_PREFLIGHT.md) and
[request drafts](PROVIDER_ACCESS_REQUEST_DRAFTS.md). Victoria and Tasmania can now progress through external review in parallel;
this is not a promised implementation order.

## Development sequence

1. Start outstanding access requests early while maintaining the released integration.
2. Investigate reproducible defects and dependency maintenance independently of
   external permissions; retain focused identity/history regression checks.
3. After access is settled, implement the next eligible provider with verified
   timestamps, categories, geometry and completeness. Keep warnings, planned burns
   and official reports distinct from satellite detections.
4. Assess other severely fire-affected countries with the same access/quality gates.
   Country priority remains a research decision, not a rollout commitment.
5. Expand the public model boundary only for a demonstrated consumer need. Do not
   publish an SDK or create another repository merely to complete the packaging pilot.

Optimization remains paused. Advanced service-side algorithms and evaporation,
solar-radiation and vegetation products are outside this integration's roadmap.
New releases and live deployment require their own validation and authorization.
