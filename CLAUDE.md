# Claude kontext — House Index

Desktop Python/PySide6 aplikácia pre hodnotenie nehnuteľností v Katowiciach. Pridávaš nehnuteľnosti (byt/dom), vypĺňaš dotazník, dostaneš numerický **Index Ideálneho Bývania** (súčet bodov podľa konfigurovateľných pravidiel). Výstup: Windows `.exe` cez PyInstaller onedir.

## Jazyk

Všetko user-facing (UI texty, error hlášky, docs) je **v slovenčine**. Kód (názvy funkcií, premenných, tabuliek) zostáva **v angličtine**.

## Tech stack

- **Python 3.11+** (dev na 3.12)
- **PySide6** (LGPL) pre GUI
- **SQLite** (WAL, `PRAGMA foreign_keys = ON`) pre štruktúrované dáta
- **Pillow** pre import/resize fotiek
- **PyInstaller** — `onedir` mode (nie onefile, aby `data/` bolo vedľa `.exe`)

## Adresárová štruktúra

```
src/house_index/
  ├── __main__.py, app.py, paths.py           # bootstrap + path resolver
  ├── db/           schema.sql, migrations.py, repository.py
  ├── domain/       models.py (dataclasses), enums.py (StrEnum)
  ├── scoring/      rules.py, engine.py, defaults.py, recompute.py
  ├── services/     property_service, photo_service, backup_service
  └── ui/           main_window, cards_view, card_delegate, detail_view,
                    compare_view, edit_dialog, settings_panel, widgets/
data/               # runtime; git-ignored. Vytvorí sa pri prvom štarte.
docs/               # VŠETKA dokumentácia sem — architecture, db_schema,
                    # scoring_methodology, user_guide, build_and_release, decisions/
tests/              # pytest; každá vrstva má vlastný test súbor
build/              # house_index.spec, version_info.txt
```

## Ako spustiť

```powershell
# Dev
.venv\Scripts\python.exe -m house_index

# Testy
.venv\Scripts\python.exe -m pytest -q

# Build .exe
.venv\Scripts\python.exe -m PyInstaller build\house_index.spec --noconfirm --clean
```

## Architektonické princípy

- **Vrstvy:** UI → Services → Repository → SQLite. Scoring je čisto-funkčná knižnica nezávislá od DB a UI.
- **SQLite per-operation:** `open_connection` je context manager, žiadna zdieľaná dlhožijúca connection medzi vláknami.
- **Prepočet indexu** po zmene configu beží v `QThread` (`ui/settings_panel.py::RecomputeWorker`).
- **`scoring/rules.py`** obsahuje **čisté funkcie** (`band_desc`, `band_asc`, `enum_score`, `bool_score`, `bool_plus_area_score`, `conditional_bool_score`). Bez side-effectov, ľahké na test.
- **`domain/models.py`** sú dataclasses (nie pydantic), ale pydantic by sa dal pridať pre validáciu.
- **`paths.py::data_dir()`** má dva módy: frozen + žiadny `portable.txt` → `%APPDATA%\HouseIndex\` (default od v0.3.0). Portable (dev alebo `portable.txt` vedľa exe) → `<app_dir>/data/`. Migrácia legacy `data/` → AppData beží raz pri prvom štarte novej verzie.
- **Auto-backup** v `services/backup_service.py::auto_backup_on_start()` — 1× denne pri štarte, 7-dňová retencia v `data/backups/`.

## Bodovací systém (scoring)

- Bodový systém: súčet bodov **bez hornej hranice** (typicky ~116 max).
- Priorita: **finančné + lokalita** majú najvyššie váhy (30 + 25 = 55 z ~116).
- Cena má pásma **by_type** — oddelené pre byt a dom.
- Konfigurácia je **ukladaná v DB** (`scoring_config` tabuľka, JSON blob, vždy jeden `is_active=1`).
- Pri zmene configu → recompute cez `services.property_service.recompute_all()`.

Pri pridávaní nového scoring parametra postupuj podľa `docs/scoring_methodology.md` (sekcia „Pridanie nového parametra”).

## Konvencie pri písaní kódu

- **Žiadne zbytočné komentáre.** Pomenovanie hovorí za seba; komentár len keď je **prečo** neobvyklé.
- **Žiadne docstring monology** — max jeden krátky riadok.
- **Žiadne backwards-compat shimy** keď nie sú potrebné.
- **Preferuj editovanie existujúcich súborov** pred vytváraním nových.
- **Neoznačuj úlohu hotovú**, ak testy nerosiatkujú alebo je UI neoverené.

## Testovanie

Coverage cieľ 85%+ pre `scoring/` a `db/repository.py`. UI sa testuje manuálne podľa checklistu v `docs/user_guide.md`.

```powershell
.venv\Scripts\python.exe -m pytest -v                       # všetko
.venv\Scripts\python.exe -m pytest tests/test_scoring_*.py  # iba scoring
```

Aktuálne **77 testov** prechádza (scoring 49, repository 10, service 8, photo 6, backup 4).

## Čo NErobiť

- **Nekommitovať `data/`** (DB + fotky). Je v `.gitignore`.
- **Nezabaľovať `onefile` PyInstaller mode** — `data/` by bolo v TEMP a data by sa strácali.
- **Pri rebuilde `.exe` NEZMAZAŤ `%APPDATA%\HouseIndex\`** — to sú user dáta. Mazať možno iba `dist/` priečinok, user dáta tam už nie sú (od v0.3.0).
- **Nevkladať scoring_config priamo do kódu** — je v DB, konfigurovateľný cez Settings UI.
- **Nemoekovať SQLite v integration testoch** — používame `sqlite:///:memory:` alebo `tmp_path`.
- **Neoznačovať `save_property` ako amending** — vždy INSERT alebo UPDATE, nikdy amend.
- **Nezmeniť schému bez migrácie** — bumpni `CURRENT_VERSION` v `db/migrations.py` a pridaj migráciu.

## Kam pridávať čo

| Zmena | Kde |
|---|---|
| Nový scoring parameter | `scoring/defaults.py` + rule funkcia v `rules.py` + field v `engine.py::_extract_value` + UI card type v `widgets/rule_card.py` + form field v `edit_dialog.py` |
| Nový UI widget | `ui/widgets/` + import v príslušnom view |
| Nová service | `services/` + import v `ui/main_window.py` alebo kde sa volá |
| Nový test | `tests/test_<modul>.py` |
| Nové docs | `docs/` (sk jazyk) |
| Zmena schémy | `db/schema.sql` + bumpni `CURRENT_VERSION` v `db/migrations.py` + pridaj migráciu |

## Rýchle pointery

- Entry point: `src/house_index/app.py::main`
- Dáta tečú: `MainWindow._on_add_property` → `PropertyEditDialog` → `PropertyService.save()` → `scoring.compute()` → `repository.save_property()` → `MainWindow.reload()`
- Default scoring config: `src/house_index/scoring/defaults.py::DEFAULT_SCORING_CONFIG`
- Farby indexu (badge): `src/house_index/ui/card_delegate.py::index_color`
- Všetky rozhodnutia: `docs/decisions/ADR-*.md`
