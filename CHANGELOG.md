# Changelog

## [0.5.0] — 2026-04-22

### Doprava — per-mode bodovanie
- Pôvodné `transit_nearest_m` (10b za najbližšiu zastávku) nahradené **tromi samostatnými pravidlami**:
  - `nearest_mhd_m` (bus / tram) — max 6b, pásma 300/600/1000/1500 m
  - `nearest_train_m` — max 5b, pásma 500/1000/2000/3000 m (vlak má voľnejšie pásma, ľudia ho používajú na diaľkové dochádzanie)
  - `nearest_regional_bus_m` — max 3b, pásma ako vlak
- Pridaný `TransitKind.REGIONAL_BUS` (regionálny/diaľkový bus). V edit dialógu pribudol v dropdowne typu zastávky.
- Engine berie **minimum per-mode** zo zoznamu zastávok (nie len globálne minimum). Byt s vlakom 800 m + tramvajou 250 m dostane body za oba módy samostatne (train 3.75 + mhd 6.0 = 9.75/14).

### Amenity — 4 nové polia na Property
- `nearest_supermarket_m` — max 8b, pásma 300/800/1500/2500 m (denná potreba)
- `nearest_kindergarten_state_m` — max 3b, pásma 500/1000/2000/3000 m
- `nearest_kindergarten_private_m` — max 2b, rovnaké pásma
- `nearest_hospital_m` — max 2b, pásma 2000/5000/10000/15000 m
- V Edit dialógu → Lokalita → nová sekcia „Amenity v okolí" so 4 spinboxmi v metroch.

### Settings — nové záložky
- **Doprava** — distance_km + 3 transport pravidlá
- **Amenity** — 4 amenity pravidlá

### Schema v2 → v3
- `ALTER TABLE properties ADD COLUMN` pre 4 amenity stĺpce.
- `transit_stops.kind` CHECK rozšírený o `regional_bus` (cez recreate table).
- Existujúce nehnuteľnosti majú 4 nové polia `NULL` — doplníš ručne v edit dialógu.
- Scoring config sa **automaticky dopĺňa** o 7 nových pravidiel, `transit_nearest_m` sa tichou migráciou odstráni.

### Celkový max index
Z ~145b (v0.4) na **~147b**. Farby badge-u (95/80/65/45) zostávajú rovnaké.

### Testy
- 109 testov (+4 pre per-mode transit extrakciu, amenity scoring, v2→v3 migráciu).

## [0.4.0] — 2026-04-22

### Karta v zozname
- **Názov nad obrázkom + indexom** — titulok cez celú šírku karty hore, pod ním fotka vľavo, detaily vpravo s index badge-om v pravom hornom rohu. Karta 320×280.
- **Odkaz na inzerát** — tlačidlo **„Otvoriť ↗"** v pravom dolnom rohu karty otvorí `primary_link` v prehliadači.
- **Cena v EUR** — pod cenou v PLN sa zobrazuje prepočet na EUR podľa aktuálneho kurzu z nastavení. Default 0.235 (apríl 2026).

### Scoring
- **Odhad nákladov na renováciu** zapracovaný do cenového pravidla. Nehnuteľnosti v stave `shell` alebo `standard` sa skórujú efektívnou cenou = `price + area_m² × odhad/m²`. Default: `shell=3 500 PLN/m²`, `standard=800 PLN/m²`, `turnkey=0`. Konfigurovateľné v Settings → Financie.
- **Stav bytu** sa teda premieta aj do finančnej časti indexu, nielen do samostatného `condition` pravidla.

### Nastavenia (Settings panel)
- **Prerobené na záložky** — Financie / Lokalita / Priestor / Vybavenie / Stav & Rok / Obecné. Každé pravidlo zostáva v príslušnej kategórii, žiadne nekonečné skrolovanie.
- **Tabuľky pásem zväčšené** — minimálne ~10 riadkov viditeľných, striedavé sfarbenie riadkov.
- **Formátovanie čísel** — hranice ako `1 000 000` namiesto `1.2e+06` (vedecký zápis). SpinBoxy s oddeľovačom tisícov, rozsah do 10 miliónov.
- **Kurz PLN → EUR** konfigurovateľný v záložke „Obecné".
- **Loading indikátor** — po kliknutí na Save sa tlačidlo okamžite disabluje, text sa zmení na „Ukladám…". Chráni pred double-click crashom.

### Logovanie
- Aplikácia loguje do `data/logs/house_index.log` (rotating, 1 MB × 3). Zachytáva aj uncaught exceptions. Pomôže pri diagnostike ak apka padne.

### Detail view
- Pridaný riadok **Cena (EUR)** a **Efektívna cena (skórovaná)** s rozdielom oproti cene pri nehnuteľnostiach v horšom stave.
- Opravené nečitateľné svetlosivé hodnoty parametrov (color `#d3d8e0` na bielom pozadí bolo nečitateľné).

### Testy
- 105 testov (+8 pre renovation cost, effective_price, EUR rate round-trip).

## [0.3.0] — 2026-04-22

### Kritická zmena ukladania dát

- **Dáta sa ukladajú do `%APPDATA%\HouseIndex\`** (Windows štandardný user-data priečinok, u teba `C:\Users\<user>\AppData\Roaming\HouseIndex\`), nie vedľa `.exe`. Rebuild `.exe` ani preinstal teraz dáta **nestratí**.
- **Automatická migrácia** — pri prvom štarte novej verzie, ak existuje starý `data/` priečinok vedľa `.exe`, obsah sa presunie do AppData.
- **Portable mód** — ak vytvoríš prázdny súbor `portable.txt` vedľa `HouseIndex.exe`, apka bude používať `data/` vedľa exe (pre USB kľúč alebo prenos).
- **Auto-backup pri štarte** — prvé spustenie každého dňa vytvorí ZIP zálohu do `data/backups/auto-<date>.zip`. Zálohy staršie ako 7 dní sa automaticky prunujú.

### Dokumentácia
- ADR-004 updated na nové default správanie.
- `user_guide.md` a `build_and_release.md` — doplnené info o AppData vs portable a auto-backup.

### Testy
- 97 testov (+15 pre paths.migrate_legacy_data, is_portable_mode, auto_backup_on_start).

## [0.2.0] — 2026-04-22

### Zmenené
- **Svetlý theme** — biele pozadie, čierny text, čitateľné záložky. Globálny stylesheet v `LIGHT_STYLESHEET`.
- **Dialogy sa vždy zmestia na obrazovku** — helper `ui/utils.py::fit_to_screen` obmedzí max veľkosť na `screen − 100 px` a vycentruje. Tab content je obalený do `QScrollArea`, takže Save/Cancel tlačidlá sú vždy viditeľné.
- **Parkovanie rozdelené** na dve samostatné polia: **Garáž** (has_garage + garage_spots) a **Parkovacie miesto** (has_parking_spot + parking_spot_count). Nehnuteľnosť môže mať obe naraz.
- **Plocha pozemku** (`plot_m2`) v záložke Základ — boduje sa iba pre dom (rule má `only_for_type: "house"`).

### Scoring zmeny
- Odstránené pravidlo `parking_kind` (enum) a `parking_spots` (band_asc).
- Pridané `garage` (bool_plus_area, base=6, per_spot=1, cap=8), `parking_spot` (base=3, per_spot=1, cap=5) a `plot_m2` (band_asc, max=8 b, iba dom).
- Celkový max body: ~124 b (predtým ~116).

### DB
- Schema version 2. Automatická migrácia v1 → v2: ALTER TABLE ADD COLUMN plus mapovanie `parking_kind` → `has_garage`/`has_parking_spot`, a DROP starých stĺpcov.

### Testy
- 82 testov (pridaných 5 pre migráciu v1 → v2).

## [0.1.0] — 2026-04-22

Prvá použiteľná verzia. Kompletný workflow: pridanie → dotazník → výpočet indexu → porovnanie → záloha.

### Pridané
- Pridávanie a úprava nehnuteľností (byt / dom) cez 6-tabový dialóg: Základ, Dotazník, Lokalita, Odkazy, Fotky, Poznámky.
- Automatický výpočet Indexu Ideálneho Bývania pri uložení pomocou bodového systému (14 pravidiel, ~116 bodov max).
- Karty s primárnou fotkou, indexom (farebný badge podľa pásma) a status pill-om.
- Radenie (index, cena, plocha, cena/m², dátum) a filtrovanie podľa statusu.
- Side-by-side porovnanie 2–3 nehnuteľností s farebným zvýraznením best/worst.
- Settings panel pre úpravu bodovania — pásma, max body, enum mapovania; zmena prepočíta index všetkým v QThread-e s progress dialogom.
- Záloha / obnova (ZIP s DB + fotky).
- SQLite úložisko s WAL a migráciami, lokálne fotky so zmenšením na max 1920 px.
- Testy: scoring (49), repository (10), photo service (6), property service (8), backup (4).

### Dokumentácia
- `docs/architecture.md`, `docs/db_schema.md`, `docs/scoring_methodology.md`, `docs/user_guide.md`, `docs/build_and_release.md`.
- 4 ADR dokumenty (PySide6, SQLite, bodový systém, PyInstaller onedir).

### Packaging
- PyInstaller onedir config v `build/house_index.spec` + `build/version_info.txt`.
