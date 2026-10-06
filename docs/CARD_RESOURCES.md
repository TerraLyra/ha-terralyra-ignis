# Dashboard card installation and updates

Bundled card delivery is available in stable 0.35.0 and later.
Use these URLs with an installed supporting version; 0.34.1 and earlier use manual files.

## One-time setup

After installing a supporting version through HACS and restarting Home Assistant,
open **Settings → Dashboards → Resources** (enable advanced mode in your profile
if needed). Add only the optional cards you use, with type **JavaScript module**:

| Card | Resource URL |
| --- | --- |
| Location summary | `/terralyra_ignis/cards/ignis-location-summary.js` |
| Report map | `/terralyra_ignis/cards/ignis-report-map.js` |
| BM OKF reports | `/terralyra_ignis/cards/ignis-bm-reports.js` |

For YAML-managed resources, use the same URLs with `type: module` in the existing
resource configuration. The native HA map needs none of these resources.

## Existing cards

Edit the existing resource URL for each card instead of adding a second entry.
This also applies to renamed local files such as `ignis-location-summary-0.33.0.js`.
Keep dashboard card YAML, entities, location IDs and other settings unchanged.
Never load both old and bundled versions of the same card in one page: whichever
registers first can win, or duplicate custom-element registration can fail.
Reload the browser fully after saving. Existing local files can remain as fallback;
no files, resource entries, automations or history are deleted automatically.

## Later updates and rollback

HACS now brings the matching card files with the integration. After an update,
restart HA at a suitable time, then reload each browser/Companion App frontend.
The resource paths remain stable, but browsers can retain older card code even
after a normal reload. HTTP serving disables long-lived cache headers; this does
not guarantee that every frontend discards its previously loaded resource.
Blueprints remain separately imported and are not overwritten.

If the installed integration version is correct but a card still shows the old
interface, edit that card's **existing** resource URL to append or replace a
version query, for example:

- `/terralyra_ignis/cards/ignis-location-summary.js?v=0.36.0`
- `/terralyra_ignis/cards/ignis-report-map.js?v=0.36.0`

Use the installed release version. Keep the JavaScript module type and only one
resource entry per card, then fully reload each browser or Companion App frontend.
The query forces a new resource URL; it does not select or install a different
integration version. No additional HA restart, file deletion or history reset is
needed for this resource-only correction.

If rolling back to 0.34.1 or earlier, restore the previous `/local/...` resource
URLs and matching local files, then reload. Those releases do not serve bundled URLs.
If a card fails to load, check the installed version, resource URL and module type,
and ensure there is exactly one resource entry for that card before reloading.

## Magyar: egyszeri átállás

Ez a megoldás a stabil 0.35.0-tól érhető el. A támogató verzió
telepítése és HA-újraindítás után a **Beállítások → Dashboardok → Erőforrások**
alatt a meglévő kártya címét cseréld a fenti táblázat megfelelő címére.
Típusa JavaScript-modul legyen. Ne adj hozzá második példányt ugyanabból a kártyából.
A dashboard és a helyszínek beállításai maradnak. Ezután töltsd újra a böngészőt.

A következő HACS-frissítések már a kártyafájlokat is hozzák; a HA újraindítása
után a böngészőt vagy a mobilalkalmazás felületét is újra kell tölteni.
Ha újratöltés után is a régi kártya látszik, a meglévő erőforráscímhez adj hozzá
verziójelölést, például `?v=0.36.0`, vagy cseréld a korábbi jelölést a telepített
verzióra. Maradjon egy bejegyzés kártyánként, JavaScript-modul típussal, majd töltsd
újra a felületet. Ez nem telepít más verziót és nem igényel újabb HA-újraindítást.
A blueprint továbbra is külön importálható. A régi helyi fájlokat nem töröljük.
0.34.1-re vagy korábbira visszaálláskor a régi erőforráscímet is vissza kell állítani.

## Development

Edit `frontend/*.js`, then run `python3 tools/sync_frontend.py` and commit the
bundled copies in `custom_components/terralyra_ignis/www/` together with the source.
CI checks byte-for-byte equality with the frontend files used by the browser tests.
Only the three named JavaScript files are served; no integration/config/storage
folder is exposed. The integration uses Home Assistant's
[asynchronous static-file API](https://developers.home-assistant.io/blog/2024/06/18/async_register_static_paths/).
