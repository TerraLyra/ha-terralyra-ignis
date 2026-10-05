"""Copy reviewed card sources into the HACS integration package before committing."""
from pathlib import Path
import shutil

root = Path(__file__).resolve().parents[1]
for name in ("ignis-bm-reports.js", "ignis-location-summary.js", "ignis-report-map.js"):
    shutil.copyfile(root / "frontend" / name,
                    root / "custom_components/terralyra_ignis/www" / name)
