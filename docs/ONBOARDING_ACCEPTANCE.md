# Public onboarding acceptance

Scope: issue #110. These checks concern usability of existing functionality,
not new providers or permission correspondence. A completed implementation is
not automatically a passed first-time-user trial.

## Delivered building blocks

| Capability | Evidence | Remaining boundary |
| --- | --- | --- |
| Separate monitoring and alert radii | 0.33.0; improved validation in 0.34.1 | Card setup review delivered; integrated onboarding acceptance remains open |
| Visual summary location selection | 0.34.0 | Visual forecast binding implemented; first-time-user acceptance remains open |
| Six-language notification blueprint | 0.34.0 | Separate import and user-selected phone; no silent automation replacement |
| Bundled optional cards | 0.35.0; resource migration observed | 0.39.0 adds an explicit administrator setup action; dashboard placement remains manual |
| Summary icons | 0.35.1 | Decoration only; no safety or official-status inference |
| Source problem guidance | 0.36.0; sampled live after browser cache recovery | Hungarian/English summary guidance implemented; broader acceptance remains open |
| Visual report-map editor and binding status | 0.36.0 | Explicit source switches remain required; all editor interactions not yet exercised live |
| Updated first-setup instructions | #133 | English/Hungarian documentation is not an unaided-user acceptance result |

The summary visual editor now reviews the selected location, both radii and
reported data availability. It explicitly states that notification setup and
delivery cannot be verified by the card. This is a card-setup review, not a full
integration onboarding wizard or notification acceptance.

The report-map editor offers only switches carrying the matching IGNIS source
metadata. Unrelated household switches are excluded. Existing explicit bindings
remain preserved for review, including older switches without metadata. Selecting
a binding does not enable its provider or turn on the switch.

## Additional delivered setup improvements (0.39.0)

PRs #158–#159 simplify unique location labels, retain disambiguation for equal
names, and provide direct settings/help links without leaving unfinished edits.
The separate registration action can add a missing module after confirmation.
Neither feature establishes first-time-user acceptance. A live preview recognized
an existing summary resource without changing it.

## Remaining acceptance work

Combined map/summary generation and regeneration shipped in 0.40.12–0.40.14.
Report-card UX improvements shipped in 0.41.3–0.41.5. Do not repeat these as
unimplemented work.

1. Exercise the delivered combined setup in the unaided trial below.
2. Validate the delivered setup review as part of the first-time-user trial:
   monitored place, both radii, source readiness and the explicit notification
   setup handoff are implemented; successful phone delivery remains unverified.
3. Review remaining report-card wording and first-time-user acceptance; the
   summary now supports Hungarian/English while preserving distinctions between
   absent observations, missing data and unavailable official restrictions.

## Unaided first-time-user trial — not yet performed

Use an isolated installation when available. Do not remove the existing production
integration, erase storage or reset history to simulate a clean installation.

- [ ] Follow FIRST_STEPS.md without developer assistance and select one place.
- [ ] Set equal radii successfully; try an alert radius larger than monitoring
  and confirm the feedback explains how to correct it without losing inputs.
- [ ] Reach a working native map, then optionally add a bundled summary card
  using one resource entry and the visual location selector.
- [ ] Confirm the summary belongs to the chosen place, including its radii.
- [ ] Import the blueprint and select the intended installation, phone and language.
  Do not send a test notification without the user's explicit agreement.
- [ ] Record any step requiring undocumented identifiers or developer assistance.

## Upgrade acceptance — partly sampled, not complete

- [ ] Compare existing entity IDs, radii and selected sources before and after update.
- [ ] Confirm old history remains available; do not delete it to make checks pass.
- [ ] Confirm bundled card updates load after browser/app reload without duplicate resources.
- [ ] Confirm existing notification automations are unchanged and not duplicated.

## Isolated resource-storage check

Automated tests use Home Assistant's real resource collection with isolated test
storage. For summary, map and BM cards, they check an empty first-run preview,
explicit creation, delayed persistence and collection reload. Repeating setup
after reload preserves the same resource ID and creates no duplicate. This does
not test browser execution or replace the unaided installation trial above.

An additional isolated test runs the integration setup, invokes concurrent
registration requests and retrieves each returned URL through the HA HTTP test
client. It confirms one resource per card and byte-for-byte bundled file delivery,
with and without a version query. This is automated technical coverage, not a
first-time-user installation result.

## Offline negative-state review

Existing automated tests cover unavailable counts, mismatched location/forecast
bindings and forecast validity. Source guidance tests cover authentication,
failed retrieval, delayed data, missing products and initialization. Maintain
these checks as the UI evolves; they do not replace a real onboarding trial.

The absence of observations must never become an all-clear. Missing restriction
data must never become “no ban”. Unknown provider states must not invent advice.

References: [first setup](FIRST_STEPS.md), [card resources](CARD_RESOURCES.md),
[release validation](NEXT_RELEASE_READINESS.md).

## Visual forecast binding

The summary editor offers explicit monitored-location FRMv3 sensors matching the
selected location. Selecting one fills the required coordinates and forecast
radius; it does not enable a provider. Unsupported or legacy saved bindings are
preserved and marked for review. Clearing the selection removes only the card
binding. No automatic forecast selection is performed.

## Map editor setup links — 0.39.1

The map editor links directly to IGNIS settings and the English/Hungarian first-setup
guide in separate tabs. Opening help does not configure providers or replace saved
map bindings. This makes setup guidance accessible without leaving the editor.

## Assisted clean-install trial — 2026-10-11

An isolated macOS Home Assistant Core 2026.9.2 instance installed stable IGNIS
0.39.1 through HACS 2.0.5. This was agent-assisted technical validation, not an
unaided-user trial or a Home Assistant OS dependency-installation test.

Verified through the UI:

- Custom repository addition, stable download and integration setup without
  optional provider credentials, using a synthetic monitoring location.
- Two available Sentinel-3 sources and zero current detections.
- Equal default 25 km radii; rejection of a 30 km alert radius against 25 km
  monitoring, followed by successful saving of a 10 km alert radius.
- Resource preview without mutation, then explicit summary/map registration.
- Visual summary location selection, correct 25/10 km values, map circles and
  hidden disabled report controls, including persistence after frontend reload.
- Version-pinned blueprint import and opening its configuration form. No phone
  was selected and no notification automation was saved or triggered.

The test Home coordinate was outside the forecast area and forecast availability
was not accepted by this trial. Live incident rendering and real phone delivery
were not established. Missing local Core dependencies were supplied separately;
this does not establish automatic dependency installation on HA OS.

The trial found stale README release wording and Hungarian summary picker metadata
on an English interface, fixed in #171. Unused report-age controls on satellite-only
maps were addressed in #172. The unaided checklist above remains open.

## New map starter configuration — delivered (#175)

New report-map cards added through the picker include monitoring and alert circles
with clustering off, so configured areas remain visible. Users can change these
options in the visual editor. Existing saved cards retain their configuration;
no report switch is automatically bound or enabled. This does not replace
first-time-user acceptance.

## Map appearance controls — delivered in 0.40.5

The visual map editor offers default, 16:9, 4:3 and square aspect ratios, plus a
scale ruler setting. Existing custom aspect ratios remain selected and are preserved
when other settings change. Default removes the override. These options only affect
presentation; locations, source switches and notification radii are unchanged.
In sections dashboards, the Layout tab can also influence card dimensions.
See the [Home Assistant map settings](https://www.home-assistant.io/dashboards/map/).

## Per-source setup review — delivered in 0.40.8

The summary editor lists source readiness and existing troubleshooting guidance
for the explicitly selected location. Unknown/unavailable sensors suppress retained
source statuses. This review is read-only and does not enable providers, change
card bindings or establish notification delivery. Hungarian and English wording
and background status transitions have automated coverage.

## Notification setup handoff — delivered in 0.40.8

The summary editor links directly to the notification-blueprint instructions in
the interface language. The guide opens separately, preserving unfinished card
edits. It explains that HACS updates do not create notification automations.
Phone selection, blueprint import and notification acceptance remain explicit
user steps; the editor does not claim delivery readiness.

## Source receipt times — delivered in 0.40.9

The editor's per-source review includes the last successful receipt timestamp in
the HA timezone. Missing or timezone-less timestamps remain unknown; invalid
formatting settings fall back to labelled UTC. Receipt time is explicitly distinct
from observation time and does not override delayed or failed source status.

## Sentinel-3 failure guidance — delivered in 0.40.11

Recognized Sentinel-3 failures have specific Hungarian/English guidance in the
summary and setup review. Successful sources ignore retained failure codes;
unknown diagnostics retain generic advice. All 51 frontend tests and 27 CI checks
passed. The post-update live check confirmed 0.40.11 and delayed-source wording,
not the failed-source messages: both Sentinel requests were successful at that
check. No production failure was injected to exercise those messages.


## Report-card upgrade acceptance — sampled on 2026-10-24

The installed version was 0.41.5. The explicit resource-refresh action updated
one existing map module and one existing BM module. After navigation loaded the
new resources, the INPE report displayed its key facts first, source-time absence
wording, collapsible technical details and readable action text on the grey theme.
The BM request returned reports; switching to all reports and selecting another
entry put its details immediately below that entry. Controls followed the English
HA interface while original Hungarian report text remained unchanged.

Before release, three theme palettes and simulated 200% text at 390px width passed
isolated browser checks. This is not a physical-phone text-scaling or full
screen-reader result. Production checks used the existing desktop layout.

Remaining accessibility acceptance:

- [ ] Physical-phone system text scaling: filter choices, detail scrolling and close action.
- [ ] Screen-reader reading order and announcements after filtering and selecting a report.
- [x] Sampled desktop keyboard activation, detail controls and Escape/Close return focus.
  Full page traversal and screen-reader acceptance remain open.

No phone notification was sent, production history removed or source setting
changed for this acceptance check. The separate unaided and reinstall trials remain open.

## Follow-up acceptance — 0.41.6–0.41.7

Sampled live checks confirmed both installed versions and explicit map-resource
refreshes. The license link was reachable by keyboard, and Escape returned focus
to the opening report marker. Report disappearance/recovery remains isolated
browser-test evidence; no production record was removed to induce the condition.

Canada recovery was verified on 2026-10-25: a successful scheduled retrieval
replaced the review-required state, returning 151 records without a storage block.
This establishes retrieval recovery, not freshness of every report or national
completeness. No history was deleted.

The current HACS validator accepts bundled brand/icon.png. PR #242 passed all 27
checks with the brands exemption removed, including HACS. This is repository
validation, not acceptance into the default HACS catalogue. The unaided setup,
separate reinstall trial and physical-phone notification checks remain open.
