# First setup / Első beállítás

[English](#english) · [Magyar](#magyar)

## English

### 1. Install and choose a place

Follow [HACS installation](../README.md#installation-through-hacs). Keep an existing
IGNIS installation when updating: do not remove its entry or history. Start with
one named place, Home or a custom location, and verify its coordinates. Add more
places later in the integration options.

In monitored-location settings, set both radii:

- **Monitoring:** how far around this place observations are tracked.
- **Alert:** how far around this place new qualifying satellite observations can
  trigger your notification automation. It must not exceed monitoring; equal is OK.

For an upgrade, preserve your previous notification distance in the alert setting.
Existing locations initially fall back to their monitoring radius unless an alert
radius has been set explicitly. [Radius details](ALERT_RADII.md).

### 2. Check data before configuring notifications

Complete source setup using the integration's available options. Optional accounts
or keys are not needed for every source; see the installation instructions. Enable
only optional report sources relevant to you and follow their documented setup.
Official reports are separate from satellite observations and do not trigger the
satellite notification blueprint.

Open the chosen place's operational-status sensor under the integration's entities.
Check the place name and source status. Initializing means wait for the first
retrieval; an access error needs the relevant credentials checked. Partial or
delayed data means coverage/freshness is limited, not that the area is safe.
An empty result is not an all-clear. [Status details](SOURCE_HEALTH.md).

### 3. Add a map and optional summary

Use the [native map example](MONITORING_RADIUS_MAP.md#recommended-map-card).
It needs no IGNIS JavaScript resource and displays satellite markers and optional
location circles. No fire markers can be a valid empty result; check source status
before interpreting it. These circles are your configured areas, not fire perimeters.

For a per-place summary, follow [card setup](LOCATION_SUMMARY_CARD.md). This optional
card requires a separate JavaScript resource. The 0.34.0 card asset includes a visual editor: select a place from its list.
If you still use the 0.33.0 file, update the existing resource separately or use
the documented explicit entity/location YAML. Forecast binding remains
an optional, separate step. Use one summary card per place.

### 4. Enable phone notifications

Import the [notification blueprint](../blueprints/automation/terralyra_ignis/satellite_alert.yaml)
from its GitHub file URL under **Settings → Automations & scenes → Blueprints**.
Select the IGNIS installation, Companion App phone and message language, then save.
The blueprint requires IGNIS 0.33.0+ and HA 2026.9+ and is imported separately from
HACS. If replacing an old notification automation, disable that old automation
explicitly to avoid duplicates. Check phone notification permissions.

Startup creates a quiet baseline: existing incidents do not generate a notification
just because HA restarted. Manual **Run actions** without an event sends nothing.
Do not treat this as a failed installation or widen the radius just to obtain a
notification. [Notification behavior](ALERT_RADII.md#event-semantics).

### Ready to use

You have checked the place, both radii and source health; the map opens; and the
notification automation uses the intended phone and language. An optional summary
shows the same place. HACS updates the integration; custom-card resources and
imported blueprints need their own update steps. Satellite notices supplement
awareness and do not replace official emergency warnings.

## Magyar

### 1. Telepítés és helyszín

Kövesd a [HACS-telepítés lépéseit](../README.md#installation-through-hacs).
Frissítéskor tartsd meg a meglévő IGNIS-bejegyzést és az előzményeket.
Kezdj egy helyszínnel: Home vagy saját pont, ellenőrzött koordinátákkal.
További helyszíneket később is hozzáadhatsz az integráció beállításaiban.

A helyszínnél állítsd be a két sugarat:

- **Megfigyelés:** ezen belül követjük az észleléseket.
- **Riasztás:** ezen belüli új, megfelelő műholdas észlelés indíthat értesítést.
  Nem lehet nagyobb a megfigyelésnél; a kettő lehet egyforma.

Frissítéskor a korábbi értesítési távolságodat őrizd meg riasztási sugárként.
Külön riasztási érték nélkül a meglévő helyszín megfigyelési sugara az alapérték.

### 2. Adatellátás ellenőrzése

Fejezd be az elérhető adatforrások beállítását. Nem minden forráshoz kell külön
fiók vagy kulcs. A számodra releváns hivatalos riportokat külön, az útmutatójuk
szerint engedélyezd; ezek nem indítják el a műholdas értesítési blueprintet.

Az integráció entitásai között nyisd meg a kiválasztott helyszín működésiállapot-
érzékelőjét. Ellenőrizd a helyszín nevét és a forrásállapotokat. Az első adatokra
várakozáskor várd meg a lekérést; hozzáférési hibánál ellenőrizd az érintett forrás
belépési adatait. A részleges vagy késő adatok korlátozott képet adnak.
A nulla észlelés nem jelent tűzmentességet.

### 3. Térkép és összefoglaló

A [natív térképpéldához](MONITORING_RADIUS_MAP.md#recommended-map-card) nem kell
külön IGNIS JavaScript-fájl. A helyszín körei a beállított sugarakat mutatják,
nem a tűz kiterjedését. Ha nincs tűzjelölő, az adatforrás állapotát is ellenőrizd.

Az opcionális [helyszínösszefoglalóhoz](LOCATION_SUMMARY_CARD.md) külön kártyafájl
és erőforrás-beállítás kell. A 0.34.0-s kártyafájl grafikus helyszínválasztót tartalmaz.
Ha még a 0.33.0-s fájlt használod, külön frissítsd a meglévő erőforrást,
vagy használd az útmutató szerinti kézi hozzárendelést. Az előrejelzés
hozzárendelése továbbra is külön, választható lépés. Helyszínenként egy kártyát adj hozzá.

### 4. Értesítési blueprint

A **Beállítások → Automatizálások és jelenetek → Blueprintek** alatt importáld
az [értesítési blueprint](../blueprints/automation/terralyra_ignis/satellite_alert.yaml)
GitHub-fájlhivatkozását. Válaszd ki az IGNIS-példányt, a Companion App telefonját
és a nyelvet, majd mentsd. IGNIS 0.33.0+ és HA 2026.9+ szükséges hozzá.
Régi értesítés cseréjekor azt külön kapcsold ki, hogy ne érkezzen dupla üzenet.
Ellenőrizd a telefon értesítési engedélyét is.

Újraindításkor a meglévő események csendes alapállapotot adnak; nem küldünk róluk
ismét értesítést. Esemény nélküli kézi indítás sem küld üzenetet. Emiatt ne növeld
meg a riasztási sugarat pusztán azért, hogy értesítést kapj.

A beállítás kész, ha a helyszín, a két sugár és a forrásállapot ellenőrzött,
a térkép megnyílik, az automatizálás pedig a kívánt telefonra és nyelvre van állítva.
A HACS az integrációt frissíti; a kártyafájl és az importált blueprint külön frissül.
Az IGNIS értesítése nem helyettesíti a hivatalos hatósági figyelmeztetést.
