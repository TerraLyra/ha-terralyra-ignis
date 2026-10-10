# Public onboarding acceptance

Scope: issue #110. These checks concern usability of existing functionality,
not new providers or permission correspondence. A completed implementation is
not automatically a passed first-time-user trial.

## Delivered building blocks

| Capability | Evidence | Remaining boundary |
| --- | --- | --- |
| Separate monitoring and alert radii | 0.33.0; improved validation in 0.34.1 | Integrated guided setup and completion summary remain open |
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

## Next implementation work

1. Reduce manual map/summary setup while retaining explicit location bindings.
2. Provide a clear setup-completion summary: monitored place, both radii, source
   readiness and notification configuration still required.
3. Review remaining report-card wording and first-time-user acceptance; the
   summary now supports Hungarian/English while preserving distinctions between
   absent observations, missing data and unavailable official restrictions.

## First-time-user trial — not yet performed

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

## Map editor setup links — next release

The map editor links directly to IGNIS settings and the English/Hungarian first-setup
guide in separate tabs. Opening help does not configure providers or replace saved
map bindings. This makes setup guidance accessible without leaving the editor.
