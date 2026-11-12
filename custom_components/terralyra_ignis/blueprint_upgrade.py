"""Upgrade untouched official satellite alert blueprints safely."""
from __future__ import annotations

import copy
import logging
import os
from pathlib import Path
import tempfile

from homeassistant.components.automation.helpers import async_get_blueprints
from homeassistant.components.blueprint.models import Blueprint
from homeassistant.components.automation.config import AUTOMATION_BLUEPRINT_SCHEMA
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util.yaml import load_yaml_dict

_LOGGER = logging.getLogger(__name__)
_MIGRATION_DIR = Path(__file__).parent / "blueprint_migrations"


def _without_source(data: dict) -> dict:
    data = copy.deepcopy(data)
    data.get("blueprint", {}).pop("source_url", None)
    return data


def _upgrade_files(folder: Path) -> list[str]:
    """Replace only semantically identical shipped legacy files, atomically."""
    if not folder.is_dir() or folder.is_symlink():
        return []
    legacy_path = _MIGRATION_DIR / "satellite_alert_legacy.yaml"
    legacy = _without_source(Blueprint(
        load_yaml_dict(legacy_path), expected_domain="automation",
        schema=AUTOMATION_BLUEPRINT_SCHEMA,
    ).data)
    legacy_comments = {line.strip() for line in legacy_path.read_text().splitlines() if "#" in line}
    current = load_yaml_dict(_MIGRATION_DIR / "satellite_alert_current.yaml")
    upgraded = []
    for path in folder.glob("**/*.yaml"):
        try:
            if path.is_symlink() or any((folder / parent).is_symlink() for parent in path.relative_to(folder).parents if str(parent) != "."):
                continue
            original = path.read_bytes()
            if any(line.strip() not in legacy_comments for line in original.decode("utf-8").splitlines() if "#" in line):
                continue
            data = load_yaml_dict(path)
            if not isinstance(data.get("blueprint"), dict) or data["blueprint"].get("name") != legacy["blueprint"]["name"]:
                continue
            candidate = Blueprint(data, expected_domain="automation", schema=AUTOMATION_BLUEPRINT_SCHEMA)
            if _without_source(candidate.data) != legacy:
                continue
            replacement = copy.deepcopy(current)
            source = data.get("blueprint", {}).get("source_url")
            if source:
                replacement["blueprint"]["source_url"] = source
            content = Blueprint(replacement, expected_domain="automation", schema=AUTOMATION_BLUEPRINT_SCHEMA).yaml()
            fd, tmp = tempfile.mkstemp(prefix=".ignis-blueprint-", dir=path.parent)
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as output:
                    output.write(content)
                if path.read_bytes() != original:
                    continue
                os.chmod(tmp, path.stat().st_mode & 0o777)
                os.replace(tmp, path)
                upgraded.append(str(path.relative_to(folder)))
            finally:
                if os.path.exists(tmp):
                    os.unlink(tmp)
        except (OSError, ValueError, TypeError, KeyError, HomeAssistantError, UnicodeError):
            _LOGGER.exception("Could not safely update blueprint %s", path)
    return upgraded


async def async_upgrade_imported_blueprints(hass: HomeAssistant) -> None:
    """Reload automation configuration after safe migration, if available."""
    folder = Path(hass.config.path("blueprints", "automation"))
    updated = await hass.async_add_executor_job(_upgrade_files, folder)
    if not updated:
        return
    _LOGGER.info("Updated unmodified IGNIS blueprints: %s", ", ".join(updated))
    if hass.services.has_service("automation", "reload"):
        await async_get_blueprints(hass).async_reset_cache()
        await hass.services.async_call("automation", "reload", blocking=True)
