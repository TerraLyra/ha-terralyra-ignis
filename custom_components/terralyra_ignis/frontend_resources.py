"""Serve only bundled public card assets; never rewrite dashboard resources."""
from pathlib import Path

from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

from .const import DOMAIN

CARD_FILES = (
    "ignis-bm-reports.js",
    "ignis-location-summary.js",
    "ignis-report-map.js",
)
URL_BASE = "/terralyra_ignis/cards"


async def async_register_card_paths(hass: HomeAssistant) -> None:
    """Register once per HA process; assets are updated with the integration."""
    data = hass.data.setdefault(DOMAIN, {})
    if data.get("card_paths_registered"):
        return
    # Explicit files only: never expose integration code, config or stored data.
    # Disable long-lived caching so the stable resource URL revalidates on reload.
    await hass.http.async_register_static_paths([
        StaticPathConfig(
            f"{URL_BASE}/{name}", str(Path(__file__).parent / "www" / name), False
        )
        for name in CARD_FILES
    ])
    data["card_paths_registered"] = True
