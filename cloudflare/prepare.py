"""Stage only public assets and the Python modules needed by the Cloudflare Worker."""

import json
from pathlib import Path
from shutil import copy2, copytree

from planner import load_catalog


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / ".motion-build"
SITE = BUILD / "site"
SERVER = BUILD / "server"
PAGES = (
    "index.html", "mobile-app.html", "motion-score-html.html", "motion-score-prototype.html",
    "design-flow.html", "design-flow.css", "design-flow.js", "design-pages.css", "design-pages.js",
    "mobile-app.css", "mobile-app.js", "map-integration.css", "map-integration.js",
    "motion-score-html.js", "ai-integration.js", "journey-data.js",
)


def prepare():
    SITE.mkdir(parents=True, exist_ok=True)
    SERVER.mkdir(parents=True, exist_ok=True)
    for name in PAGES:
        copy2(ROOT / name, SITE / name)
    copytree(ROOT / "design-assets", SITE / "design-assets", dirs_exist_ok=True)

    catalog = load_catalog()
    for track in catalog:
        path = Path(track["audioUrl"])
        if path.parts[:2] != ("assets", "demo-audio") or len(path.parts) != 3:
            raise ValueError("The public catalog must reference the bundled demo audio.")
        target = SITE / path
        target.parent.mkdir(parents=True, exist_ok=True)
        copy2(ROOT / path, target)

    # Use an online-only script at the same entry point as the local launcher.
    copy2(ROOT / "cloudflare/browser-records.js", SITE / "service-address.js")
    for name in ("amap_service.py", "planner.py"):
        copy2(ROOT / name, SERVER / name)
    copy2(ROOT / "cloudflare/worker.py", SERVER / "worker.py")
    data = json.dumps(catalog, ensure_ascii=False)
    (SERVER / "catalog_data.py").write_text(f"CATALOG_JSON = {data!r}\n", encoding="utf-8")


if __name__ == "__main__":
    prepare()
