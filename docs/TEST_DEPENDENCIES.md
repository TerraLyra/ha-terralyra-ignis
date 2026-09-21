# Test dependency compatibility

## PyTurboJPEG — reviewed 2026-09-21

IGNIS camera.py imports Home Assistant's Camera base class. HA's camera img_util
imports TurboJPEG at module load. The pytest plugin does not automatically install
all platform requirements merely to import a platform in the test process.

Removing the explicit test pin was tested in PR #49: 989 tests passed but
`test_platform_import[camera]` failed with ModuleNotFoundError for turbojpeg.
Keep the real platform-import test; do not replace the dependency with a mock.

The tested HA version was 2026.9.3. Its official
[camera manifest](https://github.com/home-assistant/core/blob/2026.9.3/homeassistant/components/camera/manifest.json)
requires PyTurboJPEG==1.8.3, so the test requirements retain that version. An
independent major upgrade to 2.5.0 would no longer mirror that platform requirement,
even if an import-only test happened to pass. Reassess the pin when upgrading the
HA test baseline, including any native-library compatibility requirements.

This is a test-environment dependency. The IGNIS runtime manifest is unchanged;
Home Assistant manages its own camera requirements. No live installation or user
history was changed during this investigation.
