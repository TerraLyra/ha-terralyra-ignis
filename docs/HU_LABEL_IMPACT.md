# Hungarian nearest-settlement label impact — 2026-09-25

Completed roadmap assessment using only the packaged GeoNames databases
(CC BY 4.0). Run `python tools/source_research/hu_label_impact.py` to reproduce
the JSON comparison and input hashes. No network, HA access or database writes.

## Result

On 60 synthetic grid coordinates (46–48°N, 16.5–22°E, spaced by 0.5°), adding
the Hungarian supplement changes 30 nearest-name labels. Of these, 29 select
a PPL record and one selects a PPLL record. The supplement includes 9,816 PPL,
78 PPLL, 135 PPLA2, 18 PPLA and one PPLC records. PPL alone does not establish
that a label is a familiar independent municipality.

This is a deterministic impact sample, not a Hungarian-boundary mask, real
fire sample, national coverage estimate or accuracy measurement. Coordinates
near/across borders deliberately retain global baseline candidates. The additive
comparison preserves baseline labels on equal-distance ties. A closer named
point does not prove a more useful label or an incident at that settlement.

The assessment uses great-circle distance and a baseline search box whose
50-km winner bound is checked at every sample. It is a separate offline
comparison, not a benchmark or a replacement implementation of the HA resolver.
Four focused tests cover distance, cross-border retention, ties and changed
minor-place labels; the full offline suite passes 248 tests.

## Decision

Do not switch the production nearest-settlement database yet. Name recognition
and user-facing nearest-town labels need different selection criteria. A future
runtime proposal should include reviewed examples of changed labels and an
explicit policy for small named localities, while preserving cross-border
coverage and entity/history identity. Optimization remains paused.

The scheduled development item is complete; return next to the deferred BM
independent-sample validation. No production behavior changed and no release
is necessary for this research tool.
