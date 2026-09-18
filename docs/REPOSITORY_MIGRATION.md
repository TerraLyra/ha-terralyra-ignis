# Historical repository migration

The new repository is `TerraLyra/ha-terralyra-ignis`. The integration domain
remains `terralyra_ignis`. Both repositories install into the same directory:
`/config/custom_components/terralyra_ignis`. They are not separate integrations.

## Status

The ordered switch from old-repository 0.26.3 to new-repository 0.26.4 was
exercised on one HACS 2.0.5 installation, followed by an update to 0.26.5.
The existing configuration entry, device identity and fixed device-entity count
were retained; sampled pre-switch activity and calendar entries remained visible.
This was a UI-level check, not a byte-for-byte archive/database comparison or a
backup-restore drill. Dynamic map-entity counts changed; their individual IDs
were not exhaustively compared. Other installations still need the checks below.

## Ordered switch

1. Create and verify a fresh backup covering Home Assistant settings, `.storage`,
   custom components and recorder history. Back up any external recorder database
   separately. Retain the backup encryption key. Record existing IGNIS entities,
   monitored locations and sample historical calendar entries.
2. Add `https://github.com/TerraLyra/ha-terralyra-ignis` as a HACS custom repository,
   type Integration. Do not download yet. Confirm the desired stable release is
   available and the old v0.26.3 remains available for rollback.
3. Uninstall the OLD downloaded package in HACS. Do NOT delete the IGNIS
   integration under Home Assistant Devices & services. Do not restart yet.
4. Download the NEW repository release into the same integration directory.
   Never uninstall the old package after installing the new one: this deletes
   the shared directory. Ensure only the new repository manages the installed
   package and automatic updates.
5. Restart Home Assistant after successful installation. Keep the original
   configuration entry; do not set up a second IGNIS integration.
6. Verify version, existing entity IDs, monitored locations, sensor history and
   historical calendar entries. Investigate missing data or duplicate entities
   before calling the migration complete. No manual `.storage` edits are needed.

## Rollback

If download fails before restart, reinstall old repository v0.26.3 first. If the
new package is already marked installed, uninstall it before reinstalling the
old one, for the same shared-directory reason. Preserve the configuration entry.
A whole-backup restore is a last resort because it can roll back data recorded
since the backup; it is not the default package rollback.

The old repository is retained. This release does not reset user history.

## HACS references

- https://www.hacs.dev/docs/faq/custom_repositories/
- https://github.com/hacs/integration/blob/2.0.5/custom_components/hacs/repositories/base.py
- https://github.com/hacs/integration/blob/2.0.5/custom_components/hacs/repositories/integration.py
