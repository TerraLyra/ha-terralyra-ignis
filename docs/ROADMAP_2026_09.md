# IGNIS public development roadmap

Status reviewed on 2026-09-21 against stable 0.27.1.

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
| Western Australia DFES | User confirmed access request sent on 2026-09-21 | Clarify dataset approval and distributed local authentication |
| South Australia CFS | User confirmed clarification request sent on 2026-09-21 | Resolve product-specific reuse terms |
| Northern Territory | Access preflight and enquiry draft ready | Confirm supported feed and reuse scope |

Victoria, Tasmania, Western Australia and South Australia submissions are confirmed
by the user; Northern Territory remains a draft. No approval is inferred from a publicly reachable endpoint.
See [access preflight](PROVIDER_ACCESS_PREFLIGHT.md) and
[request drafts](PROVIDER_ACCESS_REQUEST_DRAFTS.md). The submitted requests can progress through external review in parallel;
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

## Maintenance release 0.27.1

Source retrieval diagnostics for current counts and the partial-restart regression
shipped in 0.27.1. Sampled live checks confirmed all three count types expose the
new attributes. See [release validation](NEXT_RELEASE_READINESS.md).

## Country-level place-name coverage (approved 2026-09-24)

- [x] Start with Hungary: filtered GeoNames country supplement, stable upstream
  identifiers, attribution, reproducible build and offline BM name-review option.
- [ ] Validate Hungary against new independent BM RSS notices, including inflected
  names, homonyms, route references and responding-unit names. Name recognition
  alone must not authorize an incident marker or a fire classification.
- [ ] Extend other countries when a provider demonstrates missing place coverage.
  Review source/license, feature selection, package size, language-specific aliases
  and ambiguity per country. Reuse the existing GeoNames build approach; do not
  load the full world extract by default.
- [x] Assess whether richer data should also serve nearest-settlement labels;
  check label changes separately before changing that runtime behavior.

The Hungarian supplement is available to research tooling only. Production BM
map wiring, release publication and HA installation remain separate steps.

## BM fire scope (requested 2026-09-24)

- [x] Add offline evidence-only vegetation/local-asset/mixed/unknown categorization.
- [ ] Validate on independent vegetation-fire reports; distinguish burned area
  from threatened/property area before setting any large-extent flag.
- [ ] Prepare an optional landscape-fire-focused view retaining uncertain and
  mixed reports for review. Do not discard source records or user history.

## Work ordering update — 2026-09-25

At the user's request, further independent BM sample validation was deferred
until the next development item completes. Existing Érd/Törökbálint alias changes
remain offline research; they do not authorize production geolocation.

The next item, nearest-settlement label impact assessment, is now complete.
See [Hungarian label impact](HU_LABEL_IMPACT.md). Keep the runtime resolver
unchanged: a denser gazetteer has not been shown to improve label usefulness.
Return to BM independent samples after this item; there is no new release or
production installation from this assessment.

### 2026-09-25 follow-up

The user deferred additional BM validation again after the initial return sample.
Keep independent vegetation-fire validation open for a later session; do not
promote the offline location candidates to production. The user confirms that
no replies to the submitted provider enquiries have arrived yet.
