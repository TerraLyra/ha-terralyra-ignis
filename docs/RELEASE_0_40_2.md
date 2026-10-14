# 0.40.2 — Home forecast binding repair

When a saved Home forecast sample point changes, the summary card correctly
withholds the mismatched forecast. Its visual editor now offers an explicit
**Update Home forecast sample point** button, so repairing an existing binding
does not require editing YAML.

Review the displayed coordinates and apply them only if the forecast still
belongs to that location. Unavailable or invalid metadata does not offer a
refresh. The button reads current coordinates when clicked and preserves the
existing entity and location identity. Nothing changes automatically.

Update through HACS, restart Home Assistant, then fully reload the browser.
If an existing manually registered card resource remains cached, follow
[CARD_RESOURCES.md](CARD_RESOURCES.md). No storage reset or reinitialization is
needed.

Validation: 41 frontend unit tests and browser regression tests passed for
PR #185, along with all 27 reported CI checks. Tests cover unavailable metadata,
invalid coordinates, mismatched identities, no implicit mutation and latest
metadata at click time.
