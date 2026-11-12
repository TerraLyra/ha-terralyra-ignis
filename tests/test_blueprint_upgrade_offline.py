"""Verify safe migration of imported satellite alert blueprints."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from homeassistant.util.yaml import load_yaml_dict
from homeassistant.components.blueprint.models import Blueprint
from homeassistant.components.automation.config import AUTOMATION_BLUEPRINT_SCHEMA

MODULE = Path(__file__).resolve().parents[1] / 'custom_components/terralyra_ignis/blueprint_upgrade.py'
spec = spec_from_file_location('ignis_blueprint_upgrade', MODULE)
upgrade = module_from_spec(spec)
spec.loader.exec_module(upgrade)


class UpgradeTests(unittest.TestCase):
    def test_packaged_current_blueprint_matches_public_copy(self):
        public = MODULE.parents[2] / 'blueprints/automation/terralyra_ignis/satellite_alert.yaml'
        self.assertEqual(load_yaml_dict(public), load_yaml_dict(MODULE.parent / 'blueprint_migrations/satellite_alert_current.yaml'))

    def test_official_blueprint_updated_but_custom_file_retained(self):
        legacy = (MODULE.parent / 'blueprint_migrations/satellite_alert_legacy.yaml').read_text()
        with TemporaryDirectory() as directory:
            folder = Path(directory)
            official = folder / 'official.yaml'
            official.write_text(legacy.replace('blueprint:\n', 'blueprint:\n  source_url: https://example.org/blueprint.yaml\n', 1))
            custom = folder / 'custom.yaml'
            custom.write_text(legacy.replace('mode: queued', 'mode: single'))
            before = custom.read_bytes()
            self.assertEqual(upgrade._upgrade_files(folder), ['official.yaml'])
            self.assertEqual(custom.read_bytes(), before)
            self.assertEqual(load_yaml_dict(official)['blueprint']['source_url'], 'https://example.org/blueprint.yaml')
            self.assertEqual(upgrade._upgrade_files(folder), [])

    def test_blueprint_serialized_by_home_assistant_is_updated(self):
        legacy = load_yaml_dict(MODULE.parent / 'blueprint_migrations/satellite_alert_legacy.yaml')
        blueprint = Blueprint(legacy, expected_domain='automation', schema=AUTOMATION_BLUEPRINT_SCHEMA)
        blueprint.update_metadata(source_url='https://example.org/blueprint.yaml')
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'imported.yaml'
            path.write_text(blueprint.yaml())
            self.assertEqual(upgrade._upgrade_files(Path(directory)), ['imported.yaml'])
            self.assertEqual(load_yaml_dict(path)['blueprint']['source_url'], 'https://example.org/blueprint.yaml')

    def test_user_comment_is_preserved(self):
        legacy = (MODULE.parent / 'blueprint_migrations/satellite_alert_legacy.yaml').read_text()
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'commented.yaml'
            path.write_text(legacy + "\n# My customization\n")
            self.assertEqual(upgrade._upgrade_files(Path(directory)), [])
            self.assertIn('# My customization', path.read_text())

    def test_symlink_is_not_followed(self):
        legacy = (MODULE.parent / 'blueprint_migrations/satellite_alert_legacy.yaml').read_bytes()
        with TemporaryDirectory() as directory, TemporaryDirectory() as outside:
            folder = Path(directory)
            target = Path(outside) / 'target.yaml'
            target.write_bytes(legacy)
            (folder / 'linked.yaml').symlink_to(target)
            self.assertEqual(upgrade._upgrade_files(folder), [])
            self.assertEqual(target.read_bytes(), legacy)

if __name__ == '__main__':
    unittest.main()
